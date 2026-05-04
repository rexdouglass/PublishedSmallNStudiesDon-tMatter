#!/usr/bin/env python3
"""Run concrete Figure 1 corpus/database discovery searches.

Each strategy writes one JSON target manifest under steps/searches/figure1.
The manifest keeps raw search decisions, while only plausible corpus/database
leads are emitted under ``candidates`` for safe consolidation into
CORPORA_AND_DATABASES.tsv.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
import yaml


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "steps" / "searches" / "figure1"
CONTACT_EMAIL = os.environ.get("PROVENANCE_CONTACT_EMAIL", "rexdouglass@gmail.com").strip()
USER_AGENT = (
    "PublishedSmallNStudiesDontMatter figure1 corpus search "
    f"(mailto:{CONTACT_EMAIL}; noncommercial provenance research)"
)
TIMEOUT = (15, 45)
REQUEST_DELAY = float(os.environ.get("FIGURE1_SEARCH_DELAY_SECONDS", "0.35"))

REPOSITORY_TARGET = OUT_DIR / "corporasearch-repository-osf-dataverse-replication-project-effect-size.json"
BIBLIOGRAPHIC_TARGET = OUT_DIR / "corporasearch-bibliographic-openalex-crossref-replication-database-effect-size.json"
CITATION_TARGET = OUT_DIR / "corporasearch-citation-snowball-known-replication-corpora.json"
DOMAIN_TARGET = OUT_DIR / "corporasearch-domain-multifield-replication-database-effect-size.json"
CODE_TARGET = OUT_DIR / "corporasearch-code-local-original-replication-fields.json"
REGISTRY_TARGET = OUT_DIR / "corporasearch-registry-pilot-fullscale-followup.json"
ARCHIVE_TARGET = OUT_DIR / "corporasearch-archive-known-replication-project-urls.json"
MANUAL_TARGET = OUT_DIR / "corporasearch-manual-expert-suggestion-tracker.json"

REPOSITORY_EXPANDED_TARGET = OUT_DIR / "corporasearch-repository-expanded-replication-corpus-database-package.json"
BIBLIOGRAPHIC_EXPANDED_TARGET = OUT_DIR / "corporasearch-bibliographic-expanded-replication-corpus-database.json"
CITATION_EXPANDED_TARGET = OUT_DIR / "corporasearch-citation-expanded-known-replication-databases.json"
DOMAIN_EXPANDED_TARGET = OUT_DIR / "corporasearch-domain-expanded-crossfield-replication-datasets.json"
CODE_EXPANDED_TARGET = OUT_DIR / "corporasearch-code-expanded-local-pair-field-signatures.json"
REPOSITORY_PROVIDER_EXPANDED_TARGET = (
    OUT_DIR / "corporasearch-repository-provider-expanded-zenodo-figshare-dryad-replication-corpus-database-package.json"
)
SOURCE_FAMILY_EXPANDED_TARGET = OUT_DIR / "corporasearch-sourcefamily-expanded-known-replication-project-aliases.json"
ALTERNATE_VOCAB_EXPANDED_TARGET = OUT_DIR / "corporasearch-alternate-vocab-expanded-reproduction-reanalysis-validation-followup.json"
LINK_GRAPH_TARGET = OUT_DIR / "corporasearch-linkgraph-expanded-known-corpus-paper-dois-to-datasets.json"
GPT_COVERAGE_TARGET = OUT_DIR / "corporasearch-gptcoverage-expanded-missing-source-family-targets.json"
KNOWN_GOOD_RECALL_TARGET = OUT_DIR / "corporasearch-knowngood-recall-probe-existing-figure1-sources.json"
GPT_COVERAGE_SEED_FILE = ROOT / "FIGURE1_REPLICATION_SOURCE_FAMILY_SEEDS.yml"
PLOT1_SOURCE_CATALOG = ROOT / "data/derived/effect_inflation_dataset/plot1_replication_source_catalog.csv"

PIPELINE_YML = ROOT / "PROVENANCE_PIPELINE_SINGLE_SOURCE_OF_TRUTH.yml"

TRACK_IDS = {
    "repository": "plot1_corpusdb_osf_dataverse_openicpsr_search",
    "bibliographic": "plot1_corpusdb_bibliographic_corpus_paper_search",
    "citation": "plot1_corpusdb_citation_snowball_from_known_sources",
    "domain": "plot1_corpusdb_domain_specific_meta_research_search",
    "code": "plot1_corpusdb_code_and_file_name_search",
    "registry": "plot1_corpusdb_registry_and_pilot_fullscale_search",
    "archive": "plot1_corpusdb_dead_link_and_archive_recovery",
    "manual": "plot1_corpusdb_manual_expert_suggestion_capture",
    "repository_expanded": "plot1_corpusdb_repository_expanded_search",
    "bibliographic_expanded": "plot1_corpusdb_bibliographic_expanded_search",
    "citation_expanded": "plot1_corpusdb_citation_expanded_search",
    "domain_expanded": "plot1_corpusdb_domain_expanded_search",
    "code_expanded": "plot1_corpusdb_code_expanded_search",
    "repository_provider_expanded": "plot1_corpusdb_repository_provider_expanded_search",
    "source_family_expanded": "plot1_corpusdb_known_source_family_alias_expansion",
    "alternate_vocab_expanded": "plot1_corpusdb_alternate_vocabulary_expanded_search",
    "link_graph": "plot1_corpusdb_publication_data_link_graph_search",
    "gpt_coverage_expanded": "plot1_corpusdb_gpt_coverage_source_family_search",
    "known_good_recall": "plot1_corpusdb_known_good_recall_probe",
}

REPOSITORY_QUERIES = [
    '"direct replication" data original replication',
    '"replication study" "original study" dataset',
    '"replication project" effect size sample size',
    '"registered replication report" data',
    '"Many Labs" replication data',
    '"Reproducibility Project" coded data',
    '"pilot" "full-scale" trial effect size',
    '"original" "replication" "Cohen" "N"',
    '"replication" "original_N" "replication_N"',
    '"replication" "effect_size" "sample_size"',
]

BIBLIOGRAPHIC_QUERIES = [
    '"replication database" psychology',
    '"replication database" "effect size"',
    '"database of replication studies"',
    '"replication success" "original study"',
    '"replication rates" "coded" "effect sizes"',
    '"large-scale replication" "dataset"',
    '"multi-site replication" "dataset"',
    '"replication project" "sample size" "effect size"',
    '"original and replication" "effect size" "sample size"',
    '"reproducibility project" "effect sizes"',
]

CITATION_QUERIES = [
    '"FORRT Replication Database" OR FReD',
    '"DARPA SCORE" replication database claims',
    '"LOOPR" replication project',
    '"Reproducibility Project: Psychology" dataset replication',
    '"Many Labs" replication project dataset',
    '"Social Science Replication Project" dataset',
    '"Experimental Economics Replication Project" dataset',
    '"Reproducibility Project: Cancer Biology" effect level data',
    '"registered replication report" "many labs"',
]

DOMAIN_QUERIES = [
    "psychology replication database effect size",
    "behavioral science replication dataset original study",
    "management science replication project dataset",
    "operations management replication project data",
    "economics replication project original estimates",
    "political science replication archive original replication",
    "clinical trial pilot full-scale follow-up database",
    "neuroscience replication dataset effect size sample size",
    "education replication study database",
    "preclinical replication project effect size",
]

CODE_QUERIES = [
    "original_d replication_d",
    "original_N replication_N",
    "replication_pair",
    "original_effect replication_effect",
    "smaller_N larger_N",
    "replication_success",
    "effect_size sample_size original replication",
    "direct_replication dataset",
    "paired replication table",
]

REGISTRY_QUERIES = [
    "pilot trial full-scale follow-up same intervention outcome",
    "feasibility pilot definitive trial effect size sample size",
    "trial replication original trial follow-up larger sample",
    "registered trial replication study original trial",
    "clinical trial reproducibility database",
]

ARCHIVE_QUERIES = [
    "dead links from known replication project papers",
    "discontinued project pages naming replication data",
    "old supplementary datasets referenced by replication corpus articles",
    "archived OSF Dataverse GitHub OpenICPSR package URLs",
]

MANUAL_QUERIES = [
    "user-suggested replication datasets",
    "papers or corpora mentioned in notes but not yet inventoried",
    "reviewer-suggested replication databases",
    "source families seen in article introductions, appendices, or acknowledgments",
]

REPOSITORY_EXPANDED_QUERIES = [
    '"direct replication" "original study" "dataset"',
    '"replication" "original" "sample size" "effect size"',
    '"replication project" "coded data" "original study"',
    '"paired replication" "effect size" "sample size"',
    '"replication studies" "dataset" "effect size" "original"',
    '"multi-lab replication" "dataset" "effect size"',
    '"large-scale replication project" "original study"',
    '"registered replication report" "dataset" "original study"',
    '"replications and reversals" "database"',
    '"replication package" "original" "replication" "sample size"',
    '"original_effect" "replication_effect"',
    '"original sample size" "replication sample size"',
    '"original_n" "replication_n"',
]

BIBLIOGRAPHIC_EXPANDED_QUERIES = [
    '"replication database" "original" "replication"',
    '"replication database" "sample size"',
    '"database of direct replications"',
    '"systematic replication" "database"',
    '"replication project" "coded data"',
    '"replication project" "original study" "effect size"',
    '"large-scale replication" "original study"',
    '"multi-lab replication" "original study"',
    '"registered replication report" "original study"',
    '"direct replication" "effect sizes" "dataset"',
    '"replication studies" "coded" "sample size"',
    '"replications and reversals" "data"',
    '"meta-scientific" "replication" "database"',
    '"scientific claims" "replication" "database"',
]

CITATION_EXPANDED_QUERIES = [
    '"FReD" "replication database"',
    '"FORRT" "replication database"',
    '"DARPA SCORE" "replication" "dataset"',
    '"SCORE" "scientific claims" "replication"',
    '"LOOPR" "replication"',
    '"ReplicationWiki" "replication"',
    '"ManyBabies" "replication data"',
    '"ManyPrimates" "replication data"',
    '"ManyClasses" "replication data"',
    '"Many Labs" "original study"',
    '"Social Science Replication Project" "effect size"',
    '"Experimental Economics Replication Project" "effect size"',
    '"Reproducibility Project: Cancer Biology" "effect size"',
    '"Reproducibility Project: Psychology" "original study"',
]

DOMAIN_EXPANDED_QUERIES = [
    "psychology direct replication database original study",
    "social psychology replication project coded data",
    "cognitive psychology replication dataset effect size",
    "developmental psychology replication project data",
    "language acquisition replication project data",
    "education replication dataset original study effect size",
    "special education replication database effect size",
    "economics replication project data original study",
    "experimental economics replication project data",
    "political science replication data original study",
    "management replication project original study effect size",
    "marketing replication project data original study",
    "operations management replication project data",
    "preclinical cancer biology reproducibility project effect level data",
    "clinical psychology replication project dataset sample size",
    "medicine reproducibility project replication dataset effect size",
    "neuroscience replication project data original study",
    "ecology evolution replication project data effect size",
    "software engineering replication package original replication",
    "sports exercise replication project data sample size",
]

CODE_EXPANDED_QUERIES = [
    "original_sample_size replication_sample_size",
    "original_n replication_n",
    "orig_n repl_n",
    "original_effect_size replication_effect_size",
    "orig_effect repl_effect",
    "replication_effect original_effect",
    "original_study_id replication_study_id",
    "original_paper replication_paper",
    "claim_id replication_id effect_size",
    "study_pair_id original replication",
    "replication_database",
    "replications_and_reversals",
]

REPOSITORY_PROVIDER_EXPANDED_QUERIES = [
    '"replication database" "original" "replication"',
    '"replication dataset" "original study"',
    '"replication project" "effect size" "sample size"',
    '"direct replication" "original study" "data"',
    '"registered replication report" "data"',
    '"large-scale replication" "data"',
    '"multi-lab replication" "data"',
    '"reproducibility project" "effect size"',
    '"original_effect" "replication_effect"',
    '"original_n" "replication_n"',
    '"original sample size" "replication sample size"',
    '"study_pair_id" replication',
    '"claim_id" replication "effect_size"',
]

SOURCE_FAMILY_EXPANDED_QUERIES = [
    '"FReD" "Replication Database"',
    '"FORRT" "Replication Database"',
    '"Replication Database" "original findings" "replication findings"',
    '"Reproducibility Project: Psychology" data',
    '"Reproducibility Project: Cancer Biology" "effect level data"',
    '"Many Labs" "replication data"',
    '"Many Labs 2" replication data',
    '"Many Labs 3" replication data',
    '"Many Labs 4" replication data',
    '"Many Labs 5" replication data',
    '"Registered Replication Report" "supplementary data"',
    '"RRR" "registered replication report" data',
    '"Social Science Replication Project" data',
    '"Experimental Economics Replication Project" data',
    '"ReplicationWiki" replication database',
    '"SCORE" "scientific claims" data',
    '"DARPA SCORE" "replication" data',
    '"LOOPR" replication data',
    '"ManyBabies" "replication data"',
    '"ManyPrimates" "replication data"',
    '"ManyClasses" "replication data"',
    '"Metaketa" replication data',
    '"BITSS" replication archive',
    '"EGAP" replication archive',
]

ALTERNATE_VOCAB_EXPANDED_QUERIES = [
    '"reproduction dataset" "original study"',
    '"reproduction package" "original" "effect size"',
    '"reanalysis" "original study" "replication"',
    '"robustness" "replication" "dataset"',
    '"external validation" "original study" dataset',
    '"validation study" "original" "sample size"',
    '"claim verification" dataset "effect size"',
    '"claim replication" dataset',
    '"benchmark replication" dataset',
    '"many-lab" dataset original',
    '"many lab" dataset original',
    '"multi-site" replication dataset original',
    '"multi-site" validation original study',
    '"follow-up study" "original study" "effect size"',
    '"follow-up" "original effect" sample size',
    '"definitive trial" "pilot trial" "effect size"',
    '"pilot trial" "full-scale" "sample size"',
    '"replication archive" "original study"',
    '"reproducibility dataset" "original study"',
]

LINK_GRAPH_SEED_DOIS = [
    "10.5334/jopd.101",
    "10.1126/science.aac4716",
    "10.7554/eLife.04333",
    "10.1038/s41562-018-0399-z",
    "10.1038/s41562-016-0021",
]

QUERY_FALLBACKS = {
    "repository": REPOSITORY_QUERIES,
    "bibliographic": BIBLIOGRAPHIC_QUERIES,
    "citation": CITATION_QUERIES,
    "domain": DOMAIN_QUERIES,
    "code": CODE_QUERIES,
    "registry": REGISTRY_QUERIES,
    "archive": ARCHIVE_QUERIES,
    "manual": MANUAL_QUERIES,
    "repository_expanded": REPOSITORY_EXPANDED_QUERIES,
    "bibliographic_expanded": BIBLIOGRAPHIC_EXPANDED_QUERIES,
    "citation_expanded": CITATION_EXPANDED_QUERIES,
    "domain_expanded": DOMAIN_EXPANDED_QUERIES,
    "code_expanded": CODE_EXPANDED_QUERIES,
    "repository_provider_expanded": REPOSITORY_PROVIDER_EXPANDED_QUERIES,
    "source_family_expanded": SOURCE_FAMILY_EXPANDED_QUERIES,
    "alternate_vocab_expanded": ALTERNATE_VOCAB_EXPANDED_QUERIES,
    "link_graph": LINK_GRAPH_SEED_DOIS,
    "gpt_coverage_expanded": [],
    "known_good_recall": [],
}

LOCAL_SCAN_ROOTS = [
    ROOT / "data/raw/corpus_candidates",
    ROOT / "data/raw/replication_projects",
    ROOT / "data/derived/replication_pairs",
    ROOT / "data/derived/corpus_candidates",
    ROOT / "reports/corpus_suggestion_tracker.md",
    ROOT / "reports/corpus_candidates",
]

LOCAL_TEXT_EXTENSIONS = {
    ".csv",
    ".tsv",
    ".txt",
    ".md",
    ".json",
    ".jsonl",
    ".r",
    ".rmd",
    ".py",
    ".do",
    ".m",
    ".html",
    ".xml",
    ".yml",
    ".yaml",
    ".bib",
    ".readme",
}

LOCAL_TABLE_OR_PACKAGE_EXTENSIONS = {
    ".csv",
    ".tsv",
    ".xlsx",
    ".xls",
    ".sav",
    ".dta",
    ".rds",
    ".rdata",
    ".json",
    ".zip",
    ".gz",
    ".tar",
    ".tgz",
}

LOCAL_SKIP_DIR_PARTS = {
    ".git",
    "__pycache__",
    ".ipynb_checkpoints",
    "__macosx",
    "annotations",
    "node_modules",
    "renv",
}

DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", flags=re.I)

STRONG_PHRASES = [
    "replication database",
    "database of replication",
    "replication project",
    "reproducibility project",
    "registered replication report",
    "many labs",
    "large-scale replication",
    "multi-site replication",
    "replications and reversals",
    "replication studies",
]

PAIR_TERMS = [
    "original study",
    "original studies",
    "original effect",
    "replication effect",
    "effect size",
    "sample size",
    "cohen",
    "larger sample",
    "full-scale",
    "pilot",
]

DATA_TERMS = [
    "data",
    "dataset",
    "database",
    "code",
    "workbook",
    "supplement",
    "repository",
    "osf",
    "dataverse",
]

IRRELEVANT_PATTERNS = [
    "database replication protocol",
    "database replication protocols",
    "database replication systems",
    "distributed database",
    "multi-master database replication",
    "eager database replication",
    "replicated database",
    "database systems",
    "database system",
    "database research",
    "dna replication",
    "genome replication",
    "viral replication",
    "replication fork",
    "replication strand",
    "replication-strand",
    "replication strands",
    "origin of replication",
    "postgresql",
    "database management optimization",
    "transaction processing",
    "code smell",
    "code mangler",
    "martian ripples",
]

ROOT_TABLE_RECORD_KINDS = {
    "candidate_corpus_or_database",
    "candidate_repository_package",
}

CONTEXT_OR_METHOD_PATTERNS = [
    "bayesian evaluation",
    "bayesian perspective",
    "sample size determination",
    "sample size calculations",
    "assessment of replication success",
    "estimating the reproducibility",
    "what should researchers expect",
    "statistical view of replicability",
    "predicting replication",
    "predicts replication failure",
    "prediction market",
    "forecasting",
    "forecasting of replication",
    "z-curve",
    "contextual sensitivity",
    "moderating role",
    "methods for",
    "systematic review",
    "comment on",
    "ten simple rules",
    "word of caution",
    "construct validity",
    "replication crisis",
    "sceptical p",
    "skeptical p",
    "skeptical mixture",
    "hybrid method",
    "quality science",
]

INDIVIDUAL_PAPER_PATTERNS = [
    "replication data for",
    "replication code",
    "replication package",
    "a replication of",
    "replication of and extension",
    "direct replication of",
    "replication report",
]

INDIVIDUAL_REPORT_TITLE_PATTERNS = [
    r"^registered replication report\b",
    r"^registered report:",
    r"^replication study:",
    r"^replication package\b",
    r"\bregistered replication report of\b",
    r"\breplication package for\b",
    r"\ba multi[- ]lab replication of\b",
    r"\ba large[- ]scale replication of\b",
    r"\ba direct replication of\b",
    r"\ba replication of\b",
]

CORPUS_ARTIFACT_DISAMBIGUATORS = [
    "database",
    "dataset",
    "data set",
    "data dictionary",
    "coded data",
    "source data",
    "effect level data",
    "paper level data",
    "workbook",
    "repository",
    "corpus",
    "collection",
    "replications and reversals",
]

CORPUS_SIGNAL_PATTERNS = [
    "replication database",
    "database of replication",
    "effect level data",
    "paper level data",
    "experiment level data",
    "coded data",
    "source data",
    "replication database",
    "database of replication",
    "replications and reversals",
    "replication project",
    "reproducibility project",
    "many labs",
    "multi-site registered replication report",
    "registered replication report",
    "large-scale replication",
    "multi-site replication",
    "experimental economics replication project",
]


def safe_text(value: object, max_len: int = 1500) -> str:
    if value is None:
        return ""
    text = re.sub(r"\s+", " ", str(value).replace("\t", " ")).strip()
    return text[:max_len]


def slugify(value: object, fallback: str = "candidate") -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", safe_text(value).lower()).strip("_")
    return slug[:80] or fallback


def stable_id(prefix: str, *parts: object) -> str:
    text = "\n".join(safe_text(part, max_len=5000) for part in parts)
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
    label = slugify(next((part for part in parts if safe_text(part)), prefix))
    return f"{prefix}_{label}_{digest}"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def host(url: str) -> str:
    match = re.match(r"https?://([^/]+)", safe_text(url), flags=re.I)
    return match.group(1).lower() if match else ""


def normalize_doi(value: object) -> str:
    text = safe_text(value, 1000)
    if not text:
        return ""
    text = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", text, flags=re.I).strip()
    match = DOI_RE.search(text)
    if not match:
        return ""
    doi = match.group(0).rstrip(".,;)")
    return doi.lower()


def extract_dois(*values: object) -> list[str]:
    dois: list[str] = []
    for value in values:
        for match in DOI_RE.findall(safe_text(value, 5000)):
            doi = normalize_doi(match)
            if doi and doi not in dois:
                dois.append(doi)
    return dois


def make_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json"})
    return session


def load_search_tracks() -> dict[str, dict[str, Any]]:
    if not PIPELINE_YML.exists():
        return {}
    payload = yaml.safe_load(PIPELINE_YML.read_text(encoding="utf-8")) or {}
    root = payload.get("PROVENANCE_PIPELINE_SINGLE_SOURCE_OF_TRUTH") or {}
    tracks: dict[str, dict[str, Any]] = {}
    for plan in root.get("universe_search_plans") or []:
        if plan.get("id") != "search_plan_plot1_corpora_database_discovery":
            continue
        for track in plan.get("search_tracks") or []:
            track_id = track.get("id")
            if track_id:
                tracks[str(track_id)] = track
    return tracks


def queries_for(strategy: str, tracks: dict[str, dict[str, Any]]) -> list[str]:
    if strategy == "gpt_coverage_expanded":
        queries = gpt_coverage_queries()
        if queries:
            return queries
    track = tracks.get(TRACK_IDS[strategy], {})
    queries = [safe_text(query) for query in track.get("seed_queries") or [] if safe_text(query)]
    fallback = QUERY_FALLBACKS[strategy]
    # Some YAML entries are intentionally descriptive rather than executable.
    # Keep them as manifest context, but add concrete fallback strings when the
    # track would otherwise have too few direct query terms.
    if len(queries) < 5:
        for query in fallback:
            if query not in queries:
                queries.append(query)
    return queries


def gpt_coverage_queries() -> list[str]:
    if not GPT_COVERAGE_SEED_FILE.exists():
        return []
    payload = yaml.safe_load(GPT_COVERAGE_SEED_FILE.read_text(encoding="utf-8")) or {}
    root = payload.get("FIGURE1_REPLICATION_SOURCE_FAMILY_SEEDS") or {}
    queries: list[str] = []
    for family in root.get("source_families") or []:
        if not isinstance(family, dict):
            continue
        if family.get("priority") not in {"high", "medium"}:
            continue
        for query in family.get("queries") or []:
            text = safe_text(query)
            if text and text not in queries:
                queries.append(text)
        for alias in family.get("aliases") or []:
            text = safe_text(alias)
            if text and len(text) > 3:
                query = f'"{text}"'
                if query not in queries:
                    queries.append(query)
    max_queries = int(os.environ.get("FIGURE1_GPT_COVERAGE_MAX_QUERIES", "80"))
    return queries[:max_queries]


def split_catalog_multi(value: object) -> list[str]:
    text = safe_text(value, 3000)
    if not text:
        return []
    return [part.strip() for part in re.split(r"\s*\|\s*|\s*;\s*", text) if part.strip()]


def recall_probe_phrase(value: object) -> str:
    text = safe_text(value, 220)
    text = re.sub(r"\([^)]*\)", " ", text)
    text = re.sub(r"\b(?:manual|parsed|prepared|local|public|canonical|source|dataset|data|csv|xlsx|xls|rda|rds|pdf|workbook|table|supplemental|supplement)\b", " ", text, flags=re.I)
    text = re.sub(r"[_/\\.-]+", " ", text)
    text = re.sub(r"[^A-Za-z0-9: &+,'-]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip(" -_")
    tokens = [token for token in re.split(r"\s+", text) if len(token) > 1]
    if len(tokens) < 2:
        return ""
    return " ".join(tokens[:12])


def known_good_recall_queries() -> list[str]:
    """Build exact positive-control queries from included Figure 1 sources."""
    if not PLOT1_SOURCE_CATALOG.exists():
        return []
    primary_queries: list[str] = []
    extra_queries: list[str] = []

    def add(target: list[str], query: str) -> None:
        query = safe_text(query, 220)
        if query and query not in primary_queries and query not in extra_queries:
            target.append(query)

    with PLOT1_SOURCE_CATALOG.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            try:
                kept = float(row.get("kept_for_figure") or 0)
            except ValueError:
                kept = 0.0
            if row.get("plot_inclusion_status") != "included" or kept <= 0:
                continue

            source_queries: list[str] = []
            source_extra_queries: list[str] = []

            def add_source(query: str) -> None:
                query = safe_text(query, 220)
                if query and query not in source_queries and query not in source_extra_queries:
                    source_queries.append(query)

            def add_source_extra(query: str) -> None:
                query = safe_text(query, 220)
                if query and query not in source_queries and query not in source_extra_queries:
                    source_extra_queries.append(query)

            for field in ["landing_final_urls", "raw_file", "raw_dirs", "notes"]:
                for value in split_catalog_multi(row.get(field)):
                    doi = normalize_doi(value)
                    if doi:
                        add_source(doi)

            for field in ["display_family_label", "canonical_source_label", "display_label", "source_key"]:
                phrase = recall_probe_phrase(row.get(field))
                if phrase:
                    add_source(f'"{phrase}"')

            raw_file = safe_text(row.get("raw_file"))
            if raw_file:
                phrase = recall_probe_phrase(Path(raw_file).stem)
                if phrase:
                    add_source_extra(f'"{phrase}"')

            description = safe_text(row.get("source_family_description"), 240)
            if description and any(term in description.lower() for term in ["registered replication", "replication project", "reproducibility project", "many labs"]):
                phrase = recall_probe_phrase(description.split(".")[0])
                if phrase:
                    add_source_extra(f'"{phrase}"')

            if source_queries:
                add(primary_queries, source_queries[0])
                for query in source_queries[1:]:
                    add(extra_queries, query)
            for query in source_extra_queries:
                add(extra_queries, query)

    max_queries = int(os.environ.get("FIGURE1_KNOWN_GOOD_RECALL_MAX_QUERIES", "160"))
    return (primary_queries + extra_queries)[:max_queries]


def get_json(session: requests.Session, url: str, params: dict[str, object]) -> dict[str, Any]:
    response = session.get(url, params=params, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()


def post_json(session: requests.Session, url: str, payload: dict[str, object]) -> Any:
    response = session.post(url, json=payload, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()


def abstract_from_openalex(value: dict[str, list[int]] | None) -> str:
    if not value:
        return ""
    words: list[tuple[int, str]] = []
    for word, positions in value.items():
        for position in positions:
            words.append((int(position), word))
    return " ".join(word for _, word in sorted(words))


def first_list_value(value: object) -> str:
    if isinstance(value, list) and value:
        return safe_text(value[0])
    return safe_text(value)


def score_candidate(title: str, description: str, query: str, provider: str, strategy: str) -> tuple[int, list[str]]:
    text = f"{title} {description}".lower()
    reasons: list[str] = []
    score = 0

    for phrase in STRONG_PHRASES:
        if phrase in text:
            score += 5
            reasons.append(f"strong_phrase:{phrase}")
    for term in PAIR_TERMS:
        if term in text:
            score += 2
            reasons.append(f"pair_term:{term}")
    for term in DATA_TERMS:
        if term in text:
            score += 1
            reasons.append(f"data_term:{term}")

    if re.search(r"\breplications?\b", text):
        score += 2
        reasons.append("replication_word")
    if re.search(r"\boriginal\b", text):
        score += 2
        reasons.append("original_word")
    if re.search(r"\b(effect|sample)\s+size\b", text):
        score += 2
        reasons.append("effect_or_sample_size_phrase")
    if provider in {"osf", "dataverse"} and any(term in text for term in ["data", "dataset", "code"]):
        score += 1
        reasons.append("repository_data_surface")
    if provider in {"datacite", "figshare", "zenodo", "dryad"} and any(term in text for term in ["data", "dataset", "code"]):
        score += 1
        reasons.append("dataset_metadata_surface")
    if strategy in {"bibliographic", "citation", "domain", "registry"} and any(
        term in text for term in ["database", "project", "large-scale", "multi-site"]
    ):
        score += 2
        reasons.append("metadata_corpus_signal")
    if strategy == "code" and any(term in text for term in ["workbook", "table", "csv", "tsv", "xlsx", "stata", "rds"]):
        score += 3
        reasons.append("local_table_or_code_surface")
    if strategy == "archive" and any(term in text for term in ["osf", "dataverse", "github", "openicpsr", "archive"]):
        score += 2
        reasons.append("archive_repository_surface")
    if strategy == "manual" and any(term in text for term in ["worked", "partial", "blocked", "author-request", "parser"]):
        score += 2
        reasons.append("manual_tracker_status_signal")
    if strategy == "link_graph":
        score += 4
        reasons.append("known_corpus_paper_link_graph")
    if safe_text(title).lower().startswith("replication data for:"):
        score -= 4
        reasons.append("single_article_replication_package_penalty")
    if strategy != "link_graph" and "replication" not in text and "reproducibility" not in text:
        score -= 3
        reasons.append("no_replication_language_penalty")
    if query.lower().replace('"', "") in text:
        score += 1
        reasons.append("query_phrase_in_text")

    return score, reasons


def decision_for(score: int, reasons: list[str], strategy: str) -> str:
    if "single_article_replication_package_penalty" in reasons and score < 8:
        return "reject_single_article_or_package"
    threshold_by_strategy = {
        "repository": 6,
        "code": 5,
        "archive": 5,
        "manual": 5,
        "bibliographic": 7,
        "citation": 7,
        "domain": 7,
        "registry": 7,
        "link_graph": 5,
    }
    threshold = threshold_by_strategy.get(strategy, 7)
    if score >= threshold:
        return "accept_plausible_corpus_database_lead"
    if score >= threshold - 2:
        return "defer_manual_triage"
    return "reject_low_relevance_search_hit"


def has_any(text: str, terms: list[str]) -> bool:
    lower = text.lower()
    return any(term in lower for term in terms)


def title_matches_any(title: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, title, flags=re.I) for pattern in patterns)


def classify_lead(raw: dict[str, str], strategy: str) -> dict[str, str]:
    title = raw["title"]
    description = raw["description"]
    text = f"{title} {description}".lower()
    title_text = title.lower()
    decision = raw["decision"]
    accepted = decision == "accept_plausible_corpus_database_lead"

    if has_any(text, IRRELEVANT_PATTERNS):
        return {
            "record_kind": "rejected_irrelevant_search_hit",
            "inventory_status": "rejected_irrelevant_search_hit",
            "current_scope_roles": "figure1_rejected_search_context",
            "figure1_replication_relevance": "no",
            "next_action": "none_rejected_irrelevant_search_hit",
            "classification_basis": "irrelevant_replication_language_or_false_positive",
        }

    if strategy in {"repository", "bibliographic", "citation", "domain", "registry"} and not re.search(
        r"\breplica(?:te|ted|tion|tions|bility|ble|ting)\b|\breproducib", text
    ):
        return {
            "record_kind": "rejected_irrelevant_search_hit",
            "inventory_status": "rejected_irrelevant_search_hit",
            "current_scope_roles": "figure1_rejected_search_context",
            "figure1_replication_relevance": "no",
            "next_action": "none_rejected_no_replication_language",
            "classification_basis": "no_replication_or_reproducibility_language_in_hit_metadata",
        }

    context_signal = has_any(text, CONTEXT_OR_METHOD_PATTERNS)
    artifact_signal = has_any(
        text,
        [
            "database",
            "dataset",
            "data set",
            "coded data",
            "source data",
            "effect level data",
            "paper level data",
            "workbook",
            "repository",
            "osf",
            "dataverse",
            "github",
            "figshare",
            "zenodo",
        ],
    )
    if context_signal and not artifact_signal:
        return {
            "record_kind": "candidate_context_or_methods_paper",
            "inventory_status": "catalog_only_context_lead",
            "current_scope_roles": "figure1_context_lead",
            "figure1_replication_relevance": "unknown",
            "next_action": "inspect_references_or_data_availability_for_corpus_route",
            "classification_basis": "replication_methods_or_context_paper",
        }

    individual_report_signal = title_matches_any(title_text, INDIVIDUAL_REPORT_TITLE_PATTERNS)
    corpus_artifact_signal = has_any(text, CORPUS_ARTIFACT_DISAMBIGUATORS)
    one_off_replication_package_signal = "replication package" in text and not has_any(
        text,
        [
            "replication database",
            "database of replication",
            "replications and reversals",
            "effect level data",
            "paper level data",
            "experiment level data",
            "original_effect",
            "replication_effect",
            "original_n",
            "replication_n",
            "study_pair_id",
            "claim_id",
            "many labs",
            "reproducibility project",
        ],
    )
    if one_off_replication_package_signal:
        return {
            "record_kind": "candidate_individual_paper_or_package",
            "inventory_status": "routed_to_individual_paper_search",
            "current_scope_roles": "figure1_individual_paper_candidate",
            "figure1_replication_relevance": "unknown",
            "next_action": "route_to_individual_replication_paper_worklist",
            "classification_basis": "one_off_replication_package_signal",
        }
    if individual_report_signal and not corpus_artifact_signal:
        return {
            "record_kind": "candidate_individual_paper_or_package",
            "inventory_status": "routed_to_individual_paper_search",
            "current_scope_roles": "figure1_individual_paper_candidate",
            "figure1_replication_relevance": "unknown",
            "next_action": "route_to_individual_replication_paper_worklist",
            "classification_basis": "individual_registered_or_direct_replication_report_title",
        }

    corpus_signal = has_any(text, CORPUS_SIGNAL_PATTERNS)
    if strategy == "repository" and corpus_signal and not artifact_signal:
        return {
            "record_kind": "candidate_individual_paper_or_package",
            "inventory_status": "routed_to_individual_paper_search",
            "current_scope_roles": "figure1_individual_paper_candidate",
            "figure1_replication_relevance": "unknown",
            "next_action": "route_to_individual_replication_paper_worklist",
            "classification_basis": "repository_hit_has_replication_project_language_but_no_reusable_artifact_signal",
        }
    if corpus_signal:
        return {
            "record_kind": "candidate_corpus_or_database",
            "inventory_status": "discovered_search_lead" if accepted else "needs_triage_search_lead",
            "current_scope_roles": "figure1_corpus_database_candidate",
            "figure1_replication_relevance": "yes",
            "next_action": "triage_landing_page_or_package_for_pair_table",
            "classification_basis": "corpus_database_or_project_signal",
        }

    if context_signal:
        return {
            "record_kind": "candidate_context_or_methods_paper",
            "inventory_status": "catalog_only_context_lead",
            "current_scope_roles": "figure1_context_lead",
            "figure1_replication_relevance": "unknown",
            "next_action": "inspect_references_or_data_availability_for_corpus_route",
            "classification_basis": "replication_methods_or_context_paper",
        }

    if has_any(text, INDIVIDUAL_PAPER_PATTERNS):
        return {
            "record_kind": "candidate_individual_paper_or_package",
            "inventory_status": "routed_to_individual_paper_search",
            "current_scope_roles": "figure1_individual_paper_candidate",
            "figure1_replication_relevance": "unknown",
            "next_action": "route_to_individual_replication_paper_worklist",
            "classification_basis": "individual_paper_or_one_off_package_signal",
        }

    if strategy == "repository":
        return {
            "record_kind": "candidate_repository_package",
            "inventory_status": "discovered_search_lead" if accepted else "needs_triage_search_lead",
            "current_scope_roles": "figure1_repository_package_candidate",
            "figure1_replication_relevance": "unknown",
            "next_action": "triage_repository_for_pair_table_or_individual_route",
            "classification_basis": "repository_hit_without_corpus_confirmation",
        }

    if strategy == "code":
        return {
            "record_kind": "candidate_result_table",
            "inventory_status": "needs_triage_search_lead",
            "current_scope_roles": "figure1_result_table_candidate",
            "figure1_replication_relevance": "unknown",
            "next_action": "triage_file_for_pair_table_or_source_family",
            "classification_basis": "local_file_or_header_hit_without_corpus_confirmation",
        }

    if strategy in {"archive", "manual"}:
        return {
            "record_kind": "candidate_repository_package",
            "inventory_status": "discovered_search_lead" if accepted else "needs_triage_search_lead",
            "current_scope_roles": "figure1_repository_package_candidate",
            "figure1_replication_relevance": "unknown",
            "next_action": "triage_repository_for_pair_table_or_individual_route",
            "classification_basis": f"{strategy}_artifact_without_corpus_confirmation",
        }

    if strategy == "link_graph":
        product_type = safe_text(raw.get("raw_product_type", "")).lower()
        provider_name = raw.get("provider", "")
        if artifact_signal or provider_name == "datacite_related" or product_type in {"dataset", "software", "other"}:
            return {
                "record_kind": "candidate_repository_package",
                "inventory_status": "discovered_search_lead" if accepted else "needs_triage_search_lead",
                "current_scope_roles": "figure1_repository_package_candidate",
                "figure1_replication_relevance": "unknown",
                "next_action": "triage_linked_dataset_or_software_for_pair_table",
                "classification_basis": "publication_data_or_software_link_graph_hit",
            }
        return {
            "record_kind": "candidate_context_or_methods_paper",
            "inventory_status": "catalog_only_context_lead",
            "current_scope_roles": "figure1_context_lead",
            "figure1_replication_relevance": "unknown",
            "next_action": "inspect_references_or_data_availability_for_corpus_route",
            "classification_basis": "link_graph_bibliographic_neighbor_without_artifact_signal",
        }

    if strategy == "registry" and raw.get("provider") == "clinicaltrials":
        return {
            "record_kind": "candidate_individual_paper_or_package",
            "inventory_status": "routed_to_individual_paper_search",
            "current_scope_roles": "figure1_individual_pair_or_registry_candidate",
            "figure1_replication_relevance": "unknown",
            "next_action": "route_to_individual_replication_paper_worklist",
            "classification_basis": "single_registry_record_or_trial_signal",
        }

    return {
        "record_kind": "candidate_bibliographic_paper",
        "inventory_status": "needs_triage_search_lead",
        "current_scope_roles": "figure1_bibliographic_candidate",
        "figure1_replication_relevance": "unknown",
        "next_action": "triage_article_for_database_context_or_individual_route",
        "classification_basis": "bibliographic_hit_without_corpus_confirmation",
    }


def candidate_row(raw: dict[str, str], strategy: str, target_path: Path) -> dict[str, str]:
    title = raw["title"]
    description = raw["description"]
    landing_url = raw["landing_url"]
    text = f"{title} {description}"
    provider = raw["provider"]
    query = raw["query"]
    score = raw["score"]
    reasons = raw["score_reasons"]

    prefix_by_strategy = {
        "repository": "repo_search",
        "bibliographic": "biblio_search",
        "citation": "citation_search",
        "domain": "domain_search",
        "code": "code_search",
        "registry": "registry_search",
        "archive": "archive_search",
        "manual": "manual_search",
        "link_graph": "linkgraph_search",
    }
    prefix = prefix_by_strategy.get(strategy, "search")
    source_key = raw["external_id"] or landing_url or title
    classification = classify_lead(raw, strategy)
    return {
        "corpus_database_id": stable_id(prefix, provider, source_key, title),
        "name": title,
        "record_kind": classification["record_kind"],
        "inventory_status": classification["inventory_status"],
        "source_family": f"figure1_{strategy}_search",
        "domain_or_field": "unknown",
        "description": description,
        "why_relevant": (
            f"Matched Figure 1 {strategy} search query {query!r}; "
            f"lead_classification={classification['classification_basis']}; "
            f"score={score}; reasons={reasons}"
        ),
        "plot_universe_ids": "plot1_replication_pairs",
        "current_scope_roles": classification["current_scope_roles"],
        "figure1_replication_relevance": classification["figure1_replication_relevance"],
        "figure2_published_relevance": "unknown",
        "figure3_prereg_relevance": "unknown",
        "discovery_source": f"figure1_{strategy}_{provider}_search",
        "discovery_source_path": str(target_path.relative_to(ROOT)),
        "source_key": source_key,
        "citation_key": "",
        "landing_url": landing_url,
        "raw_url": raw["raw_url"],
        "host": host(landing_url) or provider,
        "access_class": "public_metadata",
        "access_status": "search_metadata_seen",
        "local_raw_paths": "",
        "backing_files": "",
        "staged_paths": "",
        "promoted_paths": "",
        "expected_rows": "",
        "known_rows": "",
        "known_pair_rows": "",
        "known_paper_units": "",
        "known_test_rows": "",
        "result_fields_available": "unknown; search metadata only",
        "has_d_or_convertible_effect": "yes" if has_any(text, ["effect size", "cohen"]) else "unknown",
        "has_n": "yes" if has_any(text, ["sample size", " n ", "participants"]) else "unknown",
        "has_replication_pair_mapping": "yes" if has_any(text, ["original study", "original effect", "original and replication"]) else "unknown",
        "has_prereg_or_planning_info": "unknown",
        "has_publication_links": "yes" if raw.get("doi") else "unknown",
        "parser_family": "not_assigned",
        "parser_status": "not_started",
        "blocker_codes": "metadata_only_search_hit",
        "next_action": classification["next_action"],
        "notes": f"provider={provider}; external_id={raw['external_id']}; doi={raw.get('doi', '')}",
    }


def raw_result(
    *,
    strategy: str,
    provider: str,
    query: str,
    title: object,
    description: object,
    landing_url: object,
    raw_url: object = "",
    external_id: object = "",
    doi: object = "",
    extra: dict[str, object] | None = None,
) -> dict[str, str]:
    title_text = safe_text(title, 500)
    description_text = safe_text(description, 1600)
    score, reasons = score_candidate(title_text, description_text, query, provider, strategy)
    decision = decision_for(score, reasons, strategy)
    out = {
        "strategy": strategy,
        "provider": provider,
        "query": query,
        "title": title_text,
        "description": description_text,
        "landing_url": safe_text(landing_url, 1000),
        "raw_url": safe_text(raw_url, 1000),
        "external_id": safe_text(external_id, 500),
        "doi": safe_text(doi, 500),
        "score": str(score),
        "score_reasons": " | ".join(reasons),
        "decision": decision,
    }
    for key, value in (extra or {}).items():
        out[f"raw_{key}"] = safe_text(value, 1000)
    return out


def dedupe_raw(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[str] = set()
    out: list[dict[str, str]] = []
    for row in rows:
        key = row.get("doi") or row.get("external_id") or row.get("landing_url") or row.get("title")
        key = f"{row.get('provider')}::{key}".lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out


def classified_rows(raw_rows: list[dict[str, str]], strategy: str, target_path: Path) -> list[dict[str, str]]:
    accepted = [
        row
        for row in raw_rows
        if row["decision"] in {"accept_plausible_corpus_database_lead", "defer_manual_triage"}
    ]
    accepted.sort(key=lambda row: (-int(row["score"]), row["provider"], row["title"].lower()))
    return [candidate_row(row, strategy, target_path) for row in accepted]


def search_osf(
    session: requests.Session,
    queries: list[str],
    per_query: int,
    *,
    strategy: str = "repository",
) -> tuple[list[dict[str, str]], list[str]]:
    rows: list[dict[str, str]] = []
    errors: list[str] = []
    for query in queries:
        try:
            payload = get_json(
                session,
                "https://api.osf.io/v2/search/",
                {"q": query, "page[size]": per_query},
            )
            for item in payload.get("data", []):
                if not isinstance(item, dict):
                    continue
                attrs = item.get("attributes") or {}
                links = item.get("links") or {}
                rows.append(
                    raw_result(
                        strategy=strategy,
                        provider="osf",
                        query=query,
                        title=attrs.get("title", ""),
                        description=attrs.get("description", ""),
                        landing_url=links.get("html", f"https://osf.io/{item.get('id', '')}/"),
                        external_id=item.get("id", ""),
                        extra={
                            "category": attrs.get("category", ""),
                            "date_created": attrs.get("date_created", ""),
                            "date_modified": attrs.get("date_modified", ""),
                        },
                    )
                )
        except Exception as exc:
            errors.append(f"osf::{query}::{type(exc).__name__}: {exc}")
        time.sleep(REQUEST_DELAY)
    return rows, errors


def search_dataverse(
    session: requests.Session,
    queries: list[str],
    per_query: int,
    *,
    strategy: str = "repository",
) -> tuple[list[dict[str, str]], list[str]]:
    rows: list[dict[str, str]] = []
    errors: list[str] = []
    for query in queries:
        try:
            payload = get_json(
                session,
                "https://dataverse.harvard.edu/api/search",
                {"q": query, "type": "dataset", "per_page": per_query},
            )
            for item in payload.get("data", {}).get("items", []):
                if not isinstance(item, dict):
                    continue
                rows.append(
                    raw_result(
                        strategy=strategy,
                        provider="dataverse",
                        query=query,
                        title=item.get("name", ""),
                        description=item.get("description", ""),
                        landing_url=item.get("url", ""),
                        external_id=item.get("global_id", item.get("identifier_of_dataverse", "")),
                        doi=item.get("global_id", "") if str(item.get("global_id", "")).startswith("doi:") else "",
                        extra={
                            "published_at": item.get("published_at", ""),
                            "authors": "; ".join(item.get("authors", []) if isinstance(item.get("authors"), list) else []),
                        },
                    )
                )
        except Exception as exc:
            errors.append(f"dataverse::{query}::{type(exc).__name__}: {exc}")
        time.sleep(REQUEST_DELAY)
    return rows, errors


def search_openalex(
    session: requests.Session,
    queries: list[str],
    per_query: int,
    *,
    strategy: str = "bibliographic",
) -> tuple[list[dict[str, str]], list[str]]:
    rows: list[dict[str, str]] = []
    errors: list[str] = []
    for query in queries:
        try:
            payload = get_json(
                session,
                "https://api.openalex.org/works",
                {"search": query, "per-page": per_query, "mailto": CONTACT_EMAIL},
            )
            for item in payload.get("results", []):
                if not isinstance(item, dict):
                    continue
                source = ((item.get("primary_location") or {}).get("source") or {}).get("display_name", "")
                rows.append(
                    raw_result(
                        strategy=strategy,
                        provider="openalex",
                        query=query,
                        title=item.get("title", item.get("display_name", "")),
                        description=abstract_from_openalex(item.get("abstract_inverted_index")),
                        landing_url=item.get("doi") or item.get("id", ""),
                        external_id=item.get("id", ""),
                        doi=item.get("doi", ""),
                        extra={
                            "publication_year": item.get("publication_year", ""),
                            "source": source,
                            "cited_by_count": item.get("cited_by_count", ""),
                        },
                    )
                )
        except Exception as exc:
            errors.append(f"openalex::{query}::{type(exc).__name__}: {exc}")
        time.sleep(REQUEST_DELAY)
    return rows, errors


def search_crossref(
    session: requests.Session,
    queries: list[str],
    per_query: int,
    *,
    strategy: str = "bibliographic",
) -> tuple[list[dict[str, str]], list[str]]:
    rows: list[dict[str, str]] = []
    errors: list[str] = []
    for query in queries:
        try:
            payload = get_json(
                session,
                "https://api.crossref.org/works",
                {
                    "query.bibliographic": query,
                    "filter": "type:journal-article",
                    "rows": per_query,
                    "mailto": CONTACT_EMAIL,
                },
            )
            for item in payload.get("message", {}).get("items", []):
                if not isinstance(item, dict):
                    continue
                title = first_list_value(item.get("title"))
                abstract = safe_text(item.get("abstract", ""))
                container = first_list_value(item.get("container-title"))
                year = ""
                published = item.get("published-print") or item.get("published-online") or item.get("created")
                if isinstance(published, dict):
                    parts = published.get("date-parts", [[]])
                    if parts and parts[0]:
                        year = str(parts[0][0])
                rows.append(
                    raw_result(
                        strategy=strategy,
                        provider="crossref",
                        query=query,
                        title=title,
                        description=abstract,
                        landing_url=item.get("URL", ""),
                        external_id=item.get("DOI", ""),
                        doi=item.get("DOI", ""),
                        extra={
                            "published_year": year,
                            "container_title": container,
                            "publisher": item.get("publisher", ""),
                            "score": item.get("score", ""),
                        },
                    )
                )
        except Exception as exc:
            errors.append(f"crossref::{query}::{type(exc).__name__}: {exc}")
        time.sleep(REQUEST_DELAY)
    return rows, errors


def search_datacite(
    session: requests.Session,
    queries: list[str],
    per_query: int,
    *,
    strategy: str = "repository",
) -> tuple[list[dict[str, str]], list[str]]:
    rows: list[dict[str, str]] = []
    errors: list[str] = []
    for query in queries:
        try:
            payload = get_json(
                session,
                "https://api.datacite.org/dois",
                {
                    "query": query,
                    "page[size]": per_query,
                    "resource-type-id": "dataset",
                },
            )
            for item in payload.get("data", []):
                if not isinstance(item, dict):
                    continue
                attrs = item.get("attributes") or {}
                titles = attrs.get("titles") or []
                descriptions = attrs.get("descriptions") or []
                title = ""
                if titles and isinstance(titles[0], dict):
                    title = titles[0].get("title", "")
                description = ""
                if descriptions and isinstance(descriptions[0], dict):
                    description = descriptions[0].get("description", "")
                doi = attrs.get("doi", item.get("id", ""))
                rows.append(
                    raw_result(
                        strategy=strategy,
                        provider="datacite",
                        query=query,
                        title=title,
                        description=description,
                        landing_url=attrs.get("url") or (f"https://doi.org/{doi}" if doi else ""),
                        external_id=item.get("id", ""),
                        doi=doi,
                        extra={
                            "publisher": attrs.get("publisher", ""),
                            "publication_year": attrs.get("publicationYear", ""),
                            "types": json.dumps(attrs.get("types", {}), sort_keys=True),
                        },
                    )
                )
        except Exception as exc:
            errors.append(f"datacite::{query}::{type(exc).__name__}: {exc}")
        time.sleep(REQUEST_DELAY)
    return rows, errors


def search_zenodo(
    session: requests.Session,
    queries: list[str],
    per_query: int,
    *,
    strategy: str = "repository",
) -> tuple[list[dict[str, str]], list[str]]:
    rows: list[dict[str, str]] = []
    errors: list[str] = []
    for query in queries:
        try:
            payload = get_json(
                session,
                "https://zenodo.org/api/records",
                {"q": query, "size": per_query},
            )
            for item in payload.get("hits", {}).get("hits", []):
                if not isinstance(item, dict):
                    continue
                metadata = item.get("metadata") or {}
                links = item.get("links") or {}
                files = item.get("files") or []
                creators = metadata.get("creators") or []
                creator_names = []
                for creator in creators[:8]:
                    if isinstance(creator, dict) and creator.get("name"):
                        creator_names.append(str(creator.get("name")))
                rows.append(
                    raw_result(
                        strategy=strategy,
                        provider="zenodo",
                        query=query,
                        title=metadata.get("title", ""),
                        description=metadata.get("description", ""),
                        landing_url=links.get("self_html") or item.get("doi_url") or metadata.get("url", ""),
                        raw_url=links.get("self", ""),
                        external_id=item.get("id", ""),
                        doi=item.get("doi", metadata.get("doi", "")),
                        extra={
                            "publication_date": metadata.get("publication_date", ""),
                            "resource_type": json.dumps(metadata.get("resource_type", {}), sort_keys=True),
                            "creators": "; ".join(creator_names),
                            "file_count": len(files) if isinstance(files, list) else "",
                        },
                    )
                )
        except Exception as exc:
            errors.append(f"zenodo::{query}::{type(exc).__name__}: {exc}")
        time.sleep(REQUEST_DELAY)
    return rows, errors


def search_figshare(
    session: requests.Session,
    queries: list[str],
    per_query: int,
    *,
    strategy: str = "repository",
) -> tuple[list[dict[str, str]], list[str]]:
    rows: list[dict[str, str]] = []
    errors: list[str] = []
    for query in queries:
        try:
            payload = post_json(
                session,
                "https://api.figshare.com/v2/articles/search",
                {"search_for": query, "page_size": per_query},
            )
            if not isinstance(payload, list):
                continue
            for item in payload:
                if not isinstance(item, dict):
                    continue
                detail: dict[str, Any] = {}
                detail_url = item.get("url_public_api") or item.get("url")
                if detail_url:
                    try:
                        detail_response = session.get(detail_url, timeout=TIMEOUT)
                        if detail_response.ok:
                            detail_payload = detail_response.json()
                            if isinstance(detail_payload, dict):
                                detail = detail_payload
                    except Exception:
                        detail = {}
                    time.sleep(min(REQUEST_DELAY, 0.2))
                files = detail.get("files") or []
                tags = detail.get("tags") or []
                categories = detail.get("categories") or []
                description = detail.get("description") or item.get("resource_title") or item.get("defined_type_name", "")
                rows.append(
                    raw_result(
                        strategy=strategy,
                        provider="figshare",
                        query=query,
                        title=item.get("title", ""),
                        description=description,
                        landing_url=item.get("url_public_html") or item.get("url", ""),
                        raw_url=item.get("url_public_api") or item.get("url", ""),
                        external_id=item.get("id", ""),
                        doi=item.get("doi") or item.get("resource_doi", ""),
                        extra={
                            "defined_type_name": item.get("defined_type_name", ""),
                            "published_date": item.get("published_date", ""),
                            "resource_title": item.get("resource_title", ""),
                            "file_count": len(files) if isinstance(files, list) else "",
                            "tags": "; ".join(str(tag) for tag in tags[:12]) if isinstance(tags, list) else "",
                            "categories": "; ".join(
                                safe_text(category.get("title", category)) if isinstance(category, dict) else safe_text(category)
                                for category in categories[:8]
                            )
                            if isinstance(categories, list)
                            else "",
                        },
                    )
                )
        except Exception as exc:
            errors.append(f"figshare::{query}::{type(exc).__name__}: {exc}")
        time.sleep(REQUEST_DELAY)
    return rows, errors


def search_dryad(
    session: requests.Session,
    queries: list[str],
    per_query: int,
    *,
    strategy: str = "repository",
) -> tuple[list[dict[str, str]], list[str]]:
    rows: list[dict[str, str]] = []
    errors: list[str] = []
    for query in queries:
        try:
            payload = get_json(
                session,
                "https://datadryad.org/api/v2/search",
                {"q": query, "per_page": per_query},
            )
            datasets = (payload.get("_embedded") or {}).get("stash:datasets") or []
            for item in datasets:
                if not isinstance(item, dict):
                    continue
                identifier = safe_text(item.get("identifier", ""))
                doi = identifier.removeprefix("doi:") if identifier.startswith("doi:") else ""
                links = item.get("_links") or {}
                self_link = ((links.get("self") or {}).get("href") or "") if isinstance(links.get("self"), dict) else ""
                download_link = (
                    ((links.get("stash:download") or {}).get("href") or "")
                    if isinstance(links.get("stash:download"), dict)
                    else ""
                )
                authors = item.get("authors") or []
                author_names = []
                for author in authors[:8]:
                    if isinstance(author, dict):
                        name = " ".join(safe_text(author.get(part, "")) for part in ["firstName", "lastName"]).strip()
                        if name:
                            author_names.append(name)
                rows.append(
                    raw_result(
                        strategy=strategy,
                        provider="dryad",
                        query=query,
                        title=item.get("title", ""),
                        description=item.get("abstract", ""),
                        landing_url=f"https://doi.org/{doi}" if doi else f"https://datadryad.org{self_link}",
                        raw_url=f"https://datadryad.org{self_link}" if self_link else "",
                        external_id=identifier or item.get("id", ""),
                        doi=doi,
                        extra={
                            "related_publication_issn": item.get("relatedPublicationISSN", ""),
                            "storage_size": item.get("storageSize", ""),
                            "authors": "; ".join(author_names),
                            "download_url": f"https://datadryad.org{download_link}" if download_link else "",
                        },
                    )
                )
        except Exception as exc:
            errors.append(f"dryad::{query}::{type(exc).__name__}: {exc}")
        time.sleep(REQUEST_DELAY)
    return rows, errors


def datacite_title_description(attrs: dict[str, Any]) -> tuple[str, str]:
    titles = attrs.get("titles") or []
    descriptions = attrs.get("descriptions") or []
    title = ""
    if titles and isinstance(titles[0], dict):
        title = titles[0].get("title", "")
    description = ""
    if descriptions and isinstance(descriptions[0], dict):
        description = descriptions[0].get("description", "")
    return safe_text(title), safe_text(description, 1600)


def seed_dois_from_existing(max_extra: int = 35) -> list[str]:
    dois: list[str] = []
    for doi in LINK_GRAPH_SEED_DOIS:
        normalized = normalize_doi(doi)
        if normalized and normalized not in dois:
            dois.append(normalized)

    root_table = ROOT / "CORPORA_AND_DATABASES.tsv"
    if root_table.exists():
        with root_table.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            for row in reader:
                joined = " ".join(
                    safe_text(row.get(column, ""))
                    for column in [
                        "name",
                        "description",
                        "why_relevant",
                        "source_key",
                        "landing_url",
                        "raw_url",
                        "notes",
                    ]
                )
                if not re.search(r"\breplica|\breproducib|many labs|score|forrt|fred", joined, flags=re.I):
                    continue
                for doi in extract_dois(joined):
                    if doi not in dois:
                        dois.append(doi)
                        if len(dois) >= len(LINK_GRAPH_SEED_DOIS) + max_extra:
                            return dois

    for manifest in sorted(OUT_DIR.glob("corporasearch-*.json")):
        try:
            payload = json.loads(manifest.read_text(encoding="utf-8"))
        except Exception:
            continue
        for row in payload.get("candidates") or []:
            joined = " ".join(
                safe_text(row.get(column, ""))
                for column in ["name", "description", "why_relevant", "source_key", "landing_url", "raw_url", "notes"]
            )
            if not re.search(r"\breplica|\breproducib|many labs|score|forrt|fred", joined, flags=re.I):
                continue
            for doi in extract_dois(joined):
                if doi not in dois:
                    dois.append(doi)
                    if len(dois) >= len(LINK_GRAPH_SEED_DOIS) + max_extra:
                        return dois
    return dois


def search_datacite_related(
    session: requests.Session,
    seed_dois: list[str],
    per_seed: int,
) -> tuple[list[dict[str, str]], list[str]]:
    rows: list[dict[str, str]] = []
    errors: list[str] = []
    for seed_doi in seed_dois:
        query = f"relatedIdentifiers.relatedIdentifier:{seed_doi}"
        try:
            payload = get_json(
                session,
                "https://api.datacite.org/dois",
                {"query": query, "page[size]": per_seed},
            )
            for item in payload.get("data", []):
                if not isinstance(item, dict):
                    continue
                attrs = item.get("attributes") or {}
                doi = normalize_doi(attrs.get("doi", item.get("id", "")))
                if doi == seed_doi:
                    continue
                title, description = datacite_title_description(attrs)
                rows.append(
                    raw_result(
                        strategy="link_graph",
                        provider="datacite_related",
                        query=seed_doi,
                        title=title,
                        description=description,
                        landing_url=attrs.get("url") or (f"https://doi.org/{doi}" if doi else ""),
                        external_id=item.get("id", ""),
                        doi=doi,
                        extra={
                            "seed_doi": seed_doi,
                            "publisher": attrs.get("publisher", ""),
                            "publication_year": attrs.get("publicationYear", ""),
                            "types": json.dumps(attrs.get("types", {}), sort_keys=True),
                            "related_identifiers": json.dumps(attrs.get("relatedIdentifiers", [])[:8], sort_keys=True),
                        },
                    )
                )
        except Exception as exc:
            errors.append(f"datacite_related::{seed_doi}::{type(exc).__name__}: {exc}")
        time.sleep(REQUEST_DELAY)
    return rows, errors


def product_identifier_url(product: dict[str, Any]) -> tuple[str, str]:
    identifiers = product.get("Identifier") or []
    for identifier in identifiers:
        if not isinstance(identifier, dict):
            continue
        scheme = safe_text(identifier.get("IDScheme", "")).lower()
        ident = safe_text(identifier.get("ID", ""))
        url = safe_text(identifier.get("IDURL", ""))
        if scheme == "doi" and ident:
            return normalize_doi(ident), url or f"https://doi.org/{normalize_doi(ident)}"
    for identifier in identifiers:
        if isinstance(identifier, dict) and safe_text(identifier.get("IDURL", "")):
            return safe_text(identifier.get("ID", "")), safe_text(identifier.get("IDURL", ""))
    return "", ""


def search_scholexplorer_links(
    session: requests.Session,
    seed_dois: list[str],
    per_seed: int,
) -> tuple[list[dict[str, str]], list[str]]:
    rows: list[dict[str, str]] = []
    errors: list[str] = []
    for seed_doi in seed_dois:
        try:
            payload = get_json(
                session,
                "https://api.scholexplorer.openaire.eu/v3/Links",
                {"sourcePid": seed_doi, "format": "json", "page": 0},
            )
            for link in (payload.get("result") or [])[:per_seed]:
                if not isinstance(link, dict):
                    continue
                target = link.get("target") or {}
                rel = link.get("RelationshipType") or {}
                external_id, landing_url = product_identifier_url(target)
                title = safe_text(target.get("Title", ""))
                product_type = safe_text(target.get("Type", ""))
                subtype = safe_text(target.get("subType", ""))
                creators = target.get("Creator") or []
                creator_names = []
                for creator in creators[:6]:
                    if isinstance(creator, dict) and creator.get("name"):
                        creator_names.append(safe_text(creator.get("name")))
                rows.append(
                    raw_result(
                        strategy="link_graph",
                        provider="openaire_scholexplorer",
                        query=seed_doi,
                        title=title,
                        description=(
                            f"OpenAIRE ScholeXplorer link from seed DOI {seed_doi}; "
                            f"relationship={rel.get('Name', '')}/{rel.get('SubType', '')}; "
                            f"type={product_type}; subtype={subtype}; creators={'; '.join(creator_names)}"
                        ),
                        landing_url=landing_url,
                        external_id=external_id,
                        doi=external_id if external_id.startswith("10.") else "",
                        extra={
                            "seed_doi": seed_doi,
                            "relationship": json.dumps(rel, sort_keys=True),
                            "product_type": product_type,
                            "product_subtype": subtype,
                        },
                    )
                )
        except Exception as exc:
            errors.append(f"scholexplorer::{seed_doi}::{type(exc).__name__}: {exc}")
        time.sleep(REQUEST_DELAY)
    return rows, errors


def search_semantic_scholar_neighbors(
    session: requests.Session,
    seed_dois: list[str],
    per_seed: int,
) -> tuple[list[dict[str, str]], list[str]]:
    rows: list[dict[str, str]] = []
    errors: list[str] = []
    fields = (
        "title,abstract,url,externalIds,year,"
        "citations.title,citations.externalIds,citations.year,"
        "references.title,references.externalIds,references.year"
    )
    for seed_doi in seed_dois:
        try:
            payload = get_json(
                session,
                f"https://api.semanticscholar.org/graph/v1/paper/DOI:{seed_doi}",
                {"fields": fields},
            )
            for relation_name in ["citations", "references"]:
                for item in (payload.get(relation_name) or [])[:per_seed]:
                    if not isinstance(item, dict):
                        continue
                    external_ids = item.get("externalIds") or {}
                    doi = normalize_doi(external_ids.get("DOI", ""))
                    rows.append(
                        raw_result(
                            strategy="link_graph",
                            provider=f"semantic_scholar_{relation_name}",
                            query=seed_doi,
                            title=item.get("title", ""),
                            description=f"Semantic Scholar {relation_name[:-1]} neighbor for known corpus/source-family DOI {seed_doi}.",
                            landing_url=f"https://doi.org/{doi}" if doi else "",
                            external_id=doi or external_ids.get("CorpusId", ""),
                            doi=doi,
                            extra={
                                "seed_doi": seed_doi,
                                "relation": relation_name,
                                "year": item.get("year", ""),
                                "external_ids": json.dumps(external_ids, sort_keys=True),
                            },
                        )
                    )
        except Exception as exc:
            errors.append(f"semantic_scholar::{seed_doi}::{type(exc).__name__}: {exc}")
        time.sleep(max(REQUEST_DELAY, 1.0))
    return rows, errors


def search_europepmc(
    session: requests.Session,
    queries: list[str],
    per_query: int,
    *,
    strategy: str = "bibliographic",
) -> tuple[list[dict[str, str]], list[str]]:
    rows: list[dict[str, str]] = []
    errors: list[str] = []
    for query in queries:
        try:
            payload = get_json(
                session,
                "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
                {
                    "query": query,
                    "format": "json",
                    "pageSize": per_query,
                    "resultType": "core",
                },
            )
            for item in payload.get("resultList", {}).get("result", []):
                if not isinstance(item, dict):
                    continue
                pmid = safe_text(item.get("pmid", ""))
                pmcid = safe_text(item.get("pmcid", ""))
                doi = safe_text(item.get("doi", ""))
                if doi:
                    landing_url = f"https://doi.org/{doi}"
                elif pmcid:
                    landing_url = f"https://europepmc.org/article/PMC/{pmcid.removeprefix('PMC')}"
                elif pmid:
                    landing_url = f"https://europepmc.org/article/MED/{pmid}"
                else:
                    landing_url = ""
                rows.append(
                    raw_result(
                        strategy=strategy,
                        provider="europepmc",
                        query=query,
                        title=item.get("title", ""),
                        description=item.get("abstractText", ""),
                        landing_url=landing_url,
                        external_id=pmcid or pmid,
                        doi=doi,
                        extra={
                            "pmid": pmid,
                            "pmcid": pmcid,
                            "journal": item.get("journalTitle", ""),
                            "pub_year": item.get("pubYear", ""),
                        },
                    )
                )
        except Exception as exc:
            errors.append(f"europepmc::{query}::{type(exc).__name__}: {exc}")
        time.sleep(REQUEST_DELAY)
    return rows, errors


def search_clinicaltrials(
    session: requests.Session,
    queries: list[str],
    per_query: int,
) -> tuple[list[dict[str, str]], list[str]]:
    rows: list[dict[str, str]] = []
    errors: list[str] = []
    for query in queries:
        try:
            payload = get_json(
                session,
                "https://clinicaltrials.gov/api/v2/studies",
                {"query.term": query, "pageSize": per_query, "format": "json"},
            )
            for study in payload.get("studies", []):
                if not isinstance(study, dict):
                    continue
                protocol = study.get("protocolSection") or {}
                ident = protocol.get("identificationModule") or {}
                desc = protocol.get("descriptionModule") or {}
                design = protocol.get("designModule") or {}
                status = protocol.get("statusModule") or {}
                nct_id = safe_text(ident.get("nctId", ""))
                enrollment = design.get("enrollmentInfo") or {}
                title = ident.get("briefTitle") or ident.get("officialTitle") or nct_id
                summary = desc.get("briefSummary") or desc.get("detailedDescription") or ""
                rows.append(
                    raw_result(
                        strategy="registry",
                        provider="clinicaltrials",
                        query=query,
                        title=title,
                        description=summary,
                        landing_url=f"https://clinicaltrials.gov/study/{nct_id}" if nct_id else "",
                        external_id=nct_id,
                        extra={
                            "overall_status": status.get("overallStatus", ""),
                            "enrollment_count": enrollment.get("count", ""),
                            "enrollment_type": enrollment.get("type", ""),
                            "has_results": study.get("hasResults", ""),
                        },
                    )
                )
        except Exception as exc:
            errors.append(f"clinicaltrials::{query}::{type(exc).__name__}: {exc}")
        time.sleep(REQUEST_DELAY)
    return rows, errors


def openalex_work_id(value: str) -> str:
    text = safe_text(value)
    match = re.search(r"/(W\d+)$", text)
    if match:
        return match.group(1)
    if re.fullmatch(r"W\d+", text):
        return text
    return ""


def search_openalex_citation_neighborhood(
    session: requests.Session,
    queries: list[str],
    per_query: int,
) -> tuple[list[dict[str, str]], list[str]]:
    rows: list[dict[str, str]] = []
    errors: list[str] = []
    seed_ids: list[tuple[str, str]] = []
    for query in queries:
        try:
            payload = get_json(
                session,
                "https://api.openalex.org/works",
                {"search": query, "per-page": 1, "mailto": CONTACT_EMAIL},
            )
            results = payload.get("results", [])
            if results:
                work_id = openalex_work_id(results[0].get("id", ""))
                if work_id:
                    seed_ids.append((query, work_id))
        except Exception as exc:
            errors.append(f"openalex_seed::{query}::{type(exc).__name__}: {exc}")
        time.sleep(REQUEST_DELAY)

    for query, work_id in seed_ids:
        try:
            payload = get_json(
                session,
                "https://api.openalex.org/works",
                {
                    "filter": f"cites:{work_id}",
                    "per-page": per_query,
                    "sort": "cited_by_count:desc",
                    "mailto": CONTACT_EMAIL,
                },
            )
            for item in payload.get("results", []):
                if not isinstance(item, dict):
                    continue
                source = ((item.get("primary_location") or {}).get("source") or {}).get("display_name", "")
                rows.append(
                    raw_result(
                        strategy="citation",
                        provider="openalex_cites",
                        query=f"{query} -> cites:{work_id}",
                        title=item.get("title", item.get("display_name", "")),
                        description=abstract_from_openalex(item.get("abstract_inverted_index")),
                        landing_url=item.get("doi") or item.get("id", ""),
                        external_id=item.get("id", ""),
                        doi=item.get("doi", ""),
                        extra={
                            "seed_work_id": work_id,
                            "publication_year": item.get("publication_year", ""),
                            "source": source,
                            "cited_by_count": item.get("cited_by_count", ""),
                        },
                    )
                )
        except Exception as exc:
            errors.append(f"openalex_cites::{query}::{work_id}::{type(exc).__name__}: {exc}")
        time.sleep(REQUEST_DELAY)
    return rows, errors


def repo_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def should_skip_local_path(path: Path) -> bool:
    parts = {part.lower() for part in path.parts}
    if parts & LOCAL_SKIP_DIR_PARTS:
        return True
    return path.name.startswith("._")


def local_file_text(path: Path, max_bytes: int = 32_000) -> str:
    if path.suffix.lower() not in LOCAL_TEXT_EXTENSIONS:
        return ""
    try:
        if path.stat().st_size > int(os.environ.get("FIGURE1_LOCAL_SCAN_MAX_TEXT_FILE_BYTES", "2000000")):
            return ""
    except OSError:
        return ""
    try:
        data = path.read_bytes()[:max_bytes]
    except OSError:
        return ""
    if b"\x00" in data:
        return ""
    return data.decode("utf-8", errors="ignore")


def local_match_score(haystack: str, query: str) -> int:
    terms = [term.lower() for term in re.findall(r"[A-Za-z0-9_]+", query) if len(term) > 1]
    if not terms:
        return 0
    return sum(1 for term in terms if term in haystack)


def search_local_files(queries: list[str], per_query: int) -> tuple[list[dict[str, str]], list[str]]:
    rows: list[dict[str, str]] = []
    errors: list[str] = []
    candidates: dict[str, tuple[int, dict[str, str]]] = {}
    max_results = int(os.environ.get("FIGURE1_LOCAL_SCAN_MAX_RESULTS", str(max(per_query * len(queries) * 4, 80))))
    max_files = int(os.environ.get("FIGURE1_LOCAL_SCAN_MAX_FILES", "6000"))
    roots = [root for root in LOCAL_SCAN_ROOTS if root.exists()]
    files: list[Path] = []
    for root in roots:
        if len(files) >= max_files:
            break
        if root.is_file():
            files.append(root)
        else:
            try:
                for path in root.rglob("*"):
                    if len(files) >= max_files:
                        break
                    if path.is_file() and not should_skip_local_path(path):
                        files.append(path)
            except OSError as exc:
                errors.append(f"local_scan::{repo_path(root)}::{type(exc).__name__}: {exc}")

    for path in files:
        rel = repo_path(path)
        suffix = path.suffix.lower()
        if suffix not in (LOCAL_TEXT_EXTENSIONS | LOCAL_TABLE_OR_PACKAGE_EXTENSIONS) and not path.name.endswith(
            (".tar.gz", ".tar.xz")
        ):
            continue
        text = local_file_text(path)
        haystack = f"{rel}\n{text[:8000]}".lower()
        best_query = ""
        best_score = 0
        for query in queries:
            score = local_match_score(haystack, query)
            if score > best_score:
                best_query = query
                best_score = score
        if best_score == 0:
            continue
        is_table_or_package = suffix in LOCAL_TABLE_OR_PACKAGE_EXTENSIONS or path.name.endswith((".tar.gz", ".tar.xz"))
        if not is_table_or_package and not text:
            continue
        snippet = ""
        for pattern in [
            r".{0,160}original.{0,80}replication.{0,160}",
            r".{0,160}replication.{0,80}original.{0,160}",
            r".{0,160}effect[_ -]?size.{0,80}sample[_ -]?size.{0,160}",
            r".{0,160}pilot.{0,80}full[- ]?scale.{0,160}",
        ]:
            match = re.search(pattern, text, flags=re.I | re.S)
            if match:
                snippet = safe_text(match.group(0), 500)
                break
        description = (
            f"Local scan hit; file_type={'table_or_package' if is_table_or_package else 'text_or_code'}; "
            f"matched_query={best_query}; path={rel}; snippet={snippet}"
        )
        row = raw_result(
            strategy="code",
            provider="local_file",
            query=best_query,
            title=path.stem.replace("_", " "),
            description=description,
            landing_url=rel,
            raw_url=rel,
            external_id=rel,
            extra={
                "file_size": path.stat().st_size if path.exists() else "",
                "extension": suffix,
                "local_match_score": best_score,
            },
        )
        candidates[rel] = (best_score, row)

    rows = [row for _, row in sorted(candidates.values(), key=lambda item: (-item[0], item[1]["title"].lower()))]
    return rows[:max_results], errors


def root_urls(limit: int) -> list[str]:
    table = ROOT / "CORPORA_AND_DATABASES.tsv"
    if not table.exists():
        return []
    urls: list[str] = []
    with table.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            joined = " ".join(
                safe_text(row.get(column, ""))
                for column in ["inventory_status", "access_status", "blocker_codes", "notes", "host", "landing_url", "raw_url"]
            ).lower()
            if not any(term in joined for term in ["blocked", "403", "404", "dead", "missing", "osf", "dataverse", "github", "openicpsr"]):
                continue
            for column in ["landing_url", "raw_url"]:
                for url in re.split(r"\s*\|\s*", safe_text(row.get(column, ""))):
                    if url.startswith("http") and url not in urls:
                        urls.append(url)
                        if len(urls) >= limit:
                            return urls
    return urls


def search_wayback(session: requests.Session, urls: list[str], per_url: int) -> tuple[list[dict[str, str]], list[str]]:
    rows: list[dict[str, str]] = []
    errors: list[str] = []
    for url in urls:
        try:
            response = session.get(
                "https://web.archive.org/cdx/search/cdx",
                params={
                    "url": url,
                    "output": "json",
                    "fl": "timestamp,original,statuscode,mimetype,digest",
                    "filter": "statuscode:200",
                    "collapse": "digest",
                    "limit": per_url,
                },
                timeout=(8, 12),
            )
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, list) or len(payload) < 2:
                continue
            for item in payload[1:]:
                if not isinstance(item, list) or len(item) < 5:
                    continue
                timestamp, original, status_code, mime_type, digest = item[:5]
                archived = f"https://web.archive.org/web/{timestamp}/{original}"
                rows.append(
                    raw_result(
                        strategy="archive",
                        provider="wayback",
                        query=url,
                        title=f"Wayback snapshot for {original}",
                        description=(
                            "Archived repository/project URL found during Figure 1 archive recovery; "
                            f"status={status_code}; mime_type={mime_type}; digest={digest}"
                        ),
                        landing_url=archived,
                        raw_url=original,
                        external_id=f"{timestamp}:{digest}",
                        extra={"timestamp": timestamp, "mime_type": mime_type, "status_code": status_code},
                    )
                )
        except Exception as exc:
            errors.append(f"wayback::{url}::{type(exc).__name__}: {exc}")
        time.sleep(REQUEST_DELAY)
    return rows, errors


def search_manual_tracker(queries: list[str]) -> tuple[list[dict[str, str]], list[str]]:
    path = ROOT / "reports/corpus_suggestion_tracker.md"
    if not path.exists():
        return [], [f"manual_tracker_missing::{repo_path(path)}"]
    text = path.read_text(encoding="utf-8", errors="ignore")
    rows: list[dict[str, str]] = []
    sections = re.split(r"\n(?=\| [^|\n]+ \| [^|\n]+ \|)", text)
    for section in sections:
        if "|" not in section:
            continue
        lines = [line for line in section.splitlines() if line.startswith("|") and not re.match(r"^\|\s*-", line)]
        for line in lines:
            cells = [safe_text(cell) for cell in line.strip("|").split("|")]
            if len(cells) < 3:
                continue
            if cells[0].lower() in {"rank", "source"} or cells[1].lower() == "status":
                continue
            title = cells[1] if cells[0].isdigit() else cells[0]
            status = cells[2] if cells[0].isdigit() else cells[1]
            description = " | ".join(cells[:5])
            query = next((candidate for candidate in queries if local_match_score(description.lower(), candidate) > 0), queries[0])
            rows.append(
                raw_result(
                    strategy="manual",
                    provider="manual_tracker",
                    query=query,
                    title=title,
                    description=f"Manual suggestion tracker row; status={status}; row={description}",
                    landing_url=repo_path(path),
                    raw_url=repo_path(path),
                    external_id=stable_id("manual_tracker_row", title, status, description),
                    extra={"status": status},
                )
            )
    return rows, []


def write_manifest(
    path: Path,
    *,
    strategy_id: str,
    strategy: str,
    providers: list[str],
    queries: list[str],
    raw_rows: list[dict[str, str]],
    errors: list[str],
    replace: bool,
) -> bool:
    if path.exists() and not replace:
        print(f"Skipped {path.relative_to(ROOT)} because it already exists. Use --replace to rerun.", flush=True)
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    raw_rows = dedupe_raw(raw_rows)
    classified = classified_rows(raw_rows, strategy, path)
    candidates = [row for row in classified if row["record_kind"] in ROOT_TABLE_RECORD_KINDS]
    routed_or_rejected = [row for row in classified if row["record_kind"] not in ROOT_TABLE_RECORD_KINDS]
    payload = {
        "manifest_id": path.stem,
        "strategy_id": strategy_id,
        "strategy": strategy,
        "providers": providers,
        "queries": queries,
        "created_at": utc_now(),
        "user_agent": USER_AGENT,
        "raw_result_count": len(raw_rows),
        "classified_lead_count": len(classified),
        "candidate_count": len(candidates),
        "routed_or_rejected_count": len(routed_or_rejected),
        "decision_counts": {
            decision: sum(1 for row in raw_rows if row["decision"] == decision)
            for decision in sorted({row["decision"] for row in raw_rows})
        },
        "errors": errors,
        "raw_results": raw_rows,
        "routed_or_rejected_leads": routed_or_rejected,
        "candidates": candidates,
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Wrote {path.relative_to(ROOT)} ({len(candidates)} candidates from {len(raw_rows)} raw results)", flush=True)
    return True


def should_skip(path: Path, replace: bool) -> bool:
    if path.exists() and not replace:
        print(f"Skipped {path.relative_to(ROOT)} because it already exists. Use --replace to rerun.", flush=True)
        return True
    return False


def announce(message: str) -> None:
    print(message, flush=True)


def run_repository(session: requests.Session, per_query: int, replace: bool, tracks: dict[str, dict[str, Any]]) -> None:
    if should_skip(REPOSITORY_TARGET, replace):
        return
    announce("Running repository search...")
    queries = queries_for("repository", tracks)
    raw_rows: list[dict[str, str]] = []
    errors: list[str] = []
    rows, errs = search_osf(session, queries, per_query, strategy="repository")
    raw_rows.extend(rows)
    errors.extend(errs)
    rows, errs = search_dataverse(session, queries, per_query, strategy="repository")
    raw_rows.extend(rows)
    errors.extend(errs)
    rows, errs = search_datacite(session, queries, per_query, strategy="repository")
    raw_rows.extend(rows)
    errors.extend(errs)
    write_manifest(
        REPOSITORY_TARGET,
        strategy_id="plot1_corpusdb_osf_dataverse_openicpsr_search",
        strategy="repository",
        providers=["osf", "dataverse", "datacite"],
        queries=queries,
        raw_rows=raw_rows,
        errors=errors,
        replace=replace,
    )


def run_bibliographic(session: requests.Session, per_query: int, replace: bool, tracks: dict[str, dict[str, Any]]) -> None:
    if should_skip(BIBLIOGRAPHIC_TARGET, replace):
        return
    announce("Running bibliographic search...")
    queries = queries_for("bibliographic", tracks)
    raw_rows: list[dict[str, str]] = []
    errors: list[str] = []
    rows, errs = search_openalex(session, queries, per_query, strategy="bibliographic")
    raw_rows.extend(rows)
    errors.extend(errs)
    rows, errs = search_crossref(session, queries, per_query, strategy="bibliographic")
    raw_rows.extend(rows)
    errors.extend(errs)
    rows, errs = search_europepmc(session, queries, per_query, strategy="bibliographic")
    raw_rows.extend(rows)
    errors.extend(errs)
    write_manifest(
        BIBLIOGRAPHIC_TARGET,
        strategy_id="plot1_corpusdb_bibliographic_corpus_paper_search",
        strategy="bibliographic",
        providers=["openalex", "crossref", "europepmc"],
        queries=queries,
        raw_rows=raw_rows,
        errors=errors,
        replace=replace,
    )


def run_citation(session: requests.Session, per_query: int, replace: bool, tracks: dict[str, dict[str, Any]]) -> None:
    if should_skip(CITATION_TARGET, replace):
        return
    announce("Running citation snowball search...")
    queries = queries_for("citation", tracks)
    raw_rows: list[dict[str, str]] = []
    errors: list[str] = []
    rows, errs = search_openalex(session, queries, per_query, strategy="citation")
    raw_rows.extend(rows)
    errors.extend(errs)
    rows, errs = search_crossref(session, queries, per_query, strategy="citation")
    raw_rows.extend(rows)
    errors.extend(errs)
    rows, errs = search_openalex_citation_neighborhood(session, queries, per_query)
    raw_rows.extend(rows)
    errors.extend(errs)
    write_manifest(
        CITATION_TARGET,
        strategy_id="plot1_corpusdb_citation_snowball_from_known_sources",
        strategy="citation",
        providers=["openalex", "crossref", "openalex_cites"],
        queries=queries,
        raw_rows=raw_rows,
        errors=errors,
        replace=replace,
    )


def run_domain(session: requests.Session, per_query: int, replace: bool, tracks: dict[str, dict[str, Any]]) -> None:
    if should_skip(DOMAIN_TARGET, replace):
        return
    announce("Running domain-specific search...")
    queries = queries_for("domain", tracks)
    raw_rows: list[dict[str, str]] = []
    errors: list[str] = []
    rows, errs = search_openalex(session, queries, per_query, strategy="domain")
    raw_rows.extend(rows)
    errors.extend(errs)
    rows, errs = search_crossref(session, queries, per_query, strategy="domain")
    raw_rows.extend(rows)
    errors.extend(errs)
    rows, errs = search_europepmc(session, queries, per_query, strategy="domain")
    raw_rows.extend(rows)
    errors.extend(errs)
    rows, errs = search_osf(session, queries, max(1, per_query // 2), strategy="domain")
    raw_rows.extend(rows)
    errors.extend(errs)
    rows, errs = search_dataverse(session, queries, max(1, per_query // 2), strategy="domain")
    raw_rows.extend(rows)
    errors.extend(errs)
    write_manifest(
        DOMAIN_TARGET,
        strategy_id="plot1_corpusdb_domain_specific_meta_research_search",
        strategy="domain",
        providers=["openalex", "crossref", "europepmc", "osf", "dataverse"],
        queries=queries,
        raw_rows=raw_rows,
        errors=errors,
        replace=replace,
    )


def run_code(per_query: int, replace: bool, tracks: dict[str, dict[str, Any]]) -> None:
    if should_skip(CODE_TARGET, replace):
        return
    announce("Running local code/file-name search...")
    queries = queries_for("code", tracks)
    rows, errors = search_local_files(queries, per_query)
    write_manifest(
        CODE_TARGET,
        strategy_id="plot1_corpusdb_code_and_file_name_search",
        strategy="code",
        providers=["local_file"],
        queries=queries,
        raw_rows=rows,
        errors=errors,
        replace=replace,
    )


def run_registry(session: requests.Session, per_query: int, replace: bool, tracks: dict[str, dict[str, Any]]) -> None:
    if should_skip(REGISTRY_TARGET, replace):
        return
    announce("Running registry/pilot-fullscale search...")
    queries = queries_for("registry", tracks)
    raw_rows: list[dict[str, str]] = []
    errors: list[str] = []
    rows, errs = search_clinicaltrials(session, queries, per_query)
    raw_rows.extend(rows)
    errors.extend(errs)
    rows, errs = search_openalex(session, queries, per_query, strategy="registry")
    raw_rows.extend(rows)
    errors.extend(errs)
    rows, errs = search_europepmc(session, queries, per_query, strategy="registry")
    raw_rows.extend(rows)
    errors.extend(errs)
    write_manifest(
        REGISTRY_TARGET,
        strategy_id="plot1_corpusdb_registry_and_pilot_fullscale_search",
        strategy="registry",
        providers=["clinicaltrials", "openalex", "europepmc"],
        queries=queries,
        raw_rows=raw_rows,
        errors=errors,
        replace=replace,
    )


def run_archive(session: requests.Session, per_query: int, replace: bool, tracks: dict[str, dict[str, Any]]) -> None:
    if should_skip(ARCHIVE_TARGET, replace):
        return
    announce("Running archive recovery search...")
    queries = queries_for("archive", tracks)
    urls = root_urls(limit=max(per_query * 3, 8))
    rows, errors = search_wayback(session, urls, per_url=min(per_query, 3))
    write_manifest(
        ARCHIVE_TARGET,
        strategy_id="plot1_corpusdb_dead_link_and_archive_recovery",
        strategy="archive",
        providers=["wayback"],
        queries=queries + urls,
        raw_rows=rows,
        errors=errors,
        replace=replace,
    )


def run_manual(replace: bool, tracks: dict[str, dict[str, Any]]) -> None:
    if should_skip(MANUAL_TARGET, replace):
        return
    announce("Running manual suggestion tracker extraction...")
    queries = queries_for("manual", tracks)
    rows, errors = search_manual_tracker(queries)
    write_manifest(
        MANUAL_TARGET,
        strategy_id="plot1_corpusdb_manual_expert_suggestion_capture",
        strategy="manual",
        providers=["manual_tracker"],
        queries=queries,
        raw_rows=rows,
        errors=errors,
        replace=replace,
    )


def run_repository_expanded(session: requests.Session, per_query: int, replace: bool, tracks: dict[str, dict[str, Any]]) -> None:
    if should_skip(REPOSITORY_EXPANDED_TARGET, replace):
        return
    announce("Running expanded repository search...")
    queries = queries_for("repository_expanded", tracks)
    raw_rows: list[dict[str, str]] = []
    errors: list[str] = []
    rows, errs = search_osf(session, queries, per_query, strategy="repository")
    raw_rows.extend(rows)
    errors.extend(errs)
    rows, errs = search_dataverse(session, queries, per_query, strategy="repository")
    raw_rows.extend(rows)
    errors.extend(errs)
    rows, errs = search_datacite(session, queries, per_query, strategy="repository")
    raw_rows.extend(rows)
    errors.extend(errs)
    write_manifest(
        REPOSITORY_EXPANDED_TARGET,
        strategy_id="plot1_corpusdb_repository_expanded_search",
        strategy="repository",
        providers=["osf", "dataverse", "datacite"],
        queries=queries,
        raw_rows=raw_rows,
        errors=errors,
        replace=replace,
    )


def run_bibliographic_expanded(session: requests.Session, per_query: int, replace: bool, tracks: dict[str, dict[str, Any]]) -> None:
    if should_skip(BIBLIOGRAPHIC_EXPANDED_TARGET, replace):
        return
    announce("Running expanded bibliographic search...")
    queries = queries_for("bibliographic_expanded", tracks)
    raw_rows: list[dict[str, str]] = []
    errors: list[str] = []
    rows, errs = search_openalex(session, queries, per_query, strategy="bibliographic")
    raw_rows.extend(rows)
    errors.extend(errs)
    rows, errs = search_crossref(session, queries, per_query, strategy="bibliographic")
    raw_rows.extend(rows)
    errors.extend(errs)
    rows, errs = search_europepmc(session, queries, per_query, strategy="bibliographic")
    raw_rows.extend(rows)
    errors.extend(errs)
    write_manifest(
        BIBLIOGRAPHIC_EXPANDED_TARGET,
        strategy_id="plot1_corpusdb_bibliographic_expanded_search",
        strategy="bibliographic",
        providers=["openalex", "crossref", "europepmc"],
        queries=queries,
        raw_rows=raw_rows,
        errors=errors,
        replace=replace,
    )


def run_citation_expanded(session: requests.Session, per_query: int, replace: bool, tracks: dict[str, dict[str, Any]]) -> None:
    if should_skip(CITATION_EXPANDED_TARGET, replace):
        return
    announce("Running expanded citation/name snowball search...")
    queries = queries_for("citation_expanded", tracks)
    raw_rows: list[dict[str, str]] = []
    errors: list[str] = []
    rows, errs = search_openalex(session, queries, per_query, strategy="citation")
    raw_rows.extend(rows)
    errors.extend(errs)
    rows, errs = search_crossref(session, queries, per_query, strategy="citation")
    raw_rows.extend(rows)
    errors.extend(errs)
    rows, errs = search_openalex_citation_neighborhood(session, queries, per_query)
    raw_rows.extend(rows)
    errors.extend(errs)
    write_manifest(
        CITATION_EXPANDED_TARGET,
        strategy_id="plot1_corpusdb_citation_expanded_search",
        strategy="citation",
        providers=["openalex", "crossref", "openalex_cites"],
        queries=queries,
        raw_rows=raw_rows,
        errors=errors,
        replace=replace,
    )


def run_domain_expanded(session: requests.Session, per_query: int, replace: bool, tracks: dict[str, dict[str, Any]]) -> None:
    if should_skip(DOMAIN_EXPANDED_TARGET, replace):
        return
    announce("Running expanded cross-field search...")
    queries = queries_for("domain_expanded", tracks)
    raw_rows: list[dict[str, str]] = []
    errors: list[str] = []
    rows, errs = search_openalex(session, queries, per_query, strategy="domain")
    raw_rows.extend(rows)
    errors.extend(errs)
    rows, errs = search_crossref(session, queries, per_query, strategy="domain")
    raw_rows.extend(rows)
    errors.extend(errs)
    rows, errs = search_europepmc(session, queries, per_query, strategy="domain")
    raw_rows.extend(rows)
    errors.extend(errs)
    rows, errs = search_osf(session, queries, max(1, per_query // 2), strategy="domain")
    raw_rows.extend(rows)
    errors.extend(errs)
    rows, errs = search_dataverse(session, queries, max(1, per_query // 2), strategy="domain")
    raw_rows.extend(rows)
    errors.extend(errs)
    write_manifest(
        DOMAIN_EXPANDED_TARGET,
        strategy_id="plot1_corpusdb_domain_expanded_search",
        strategy="domain",
        providers=["openalex", "crossref", "europepmc", "osf", "dataverse"],
        queries=queries,
        raw_rows=raw_rows,
        errors=errors,
        replace=replace,
    )


def run_code_expanded(per_query: int, replace: bool, tracks: dict[str, dict[str, Any]]) -> None:
    if should_skip(CODE_EXPANDED_TARGET, replace):
        return
    announce("Running expanded local code/file-name search...")
    queries = queries_for("code_expanded", tracks)
    rows, errors = search_local_files(queries, per_query)
    write_manifest(
        CODE_EXPANDED_TARGET,
        strategy_id="plot1_corpusdb_code_expanded_search",
        strategy="code",
        providers=["local_file"],
        queries=queries,
        raw_rows=rows,
        errors=errors,
        replace=replace,
    )


def run_repository_provider_expanded(
    session: requests.Session,
    per_query: int,
    replace: bool,
    tracks: dict[str, dict[str, Any]],
) -> None:
    if should_skip(REPOSITORY_PROVIDER_EXPANDED_TARGET, replace):
        return
    announce("Running expanded repository-provider search...")
    queries = queries_for("repository_provider_expanded", tracks)
    raw_rows: list[dict[str, str]] = []
    errors: list[str] = []
    rows, errs = search_zenodo(session, queries, per_query, strategy="repository")
    raw_rows.extend(rows)
    errors.extend(errs)
    rows, errs = search_figshare(session, queries, per_query, strategy="repository")
    raw_rows.extend(rows)
    errors.extend(errs)
    rows, errs = search_dryad(session, queries, per_query, strategy="repository")
    raw_rows.extend(rows)
    errors.extend(errs)
    write_manifest(
        REPOSITORY_PROVIDER_EXPANDED_TARGET,
        strategy_id="plot1_corpusdb_repository_provider_expanded_search",
        strategy="repository",
        providers=["zenodo", "figshare", "dryad"],
        queries=queries,
        raw_rows=raw_rows,
        errors=errors,
        replace=replace,
    )


def run_source_family_expanded(
    session: requests.Session,
    per_query: int,
    replace: bool,
    tracks: dict[str, dict[str, Any]],
) -> None:
    if should_skip(SOURCE_FAMILY_EXPANDED_TARGET, replace):
        return
    announce("Running known source-family alias expansion...")
    queries = queries_for("source_family_expanded", tracks)
    raw_rows: list[dict[str, str]] = []
    errors: list[str] = []
    repo_per_query = max(1, min(per_query, 4))
    biblio_per_query = max(1, min(per_query, 3))
    for search_fn, provider_name in [
        (search_osf, "osf"),
        (search_dataverse, "dataverse"),
        (search_datacite, "datacite"),
        (search_zenodo, "zenodo"),
        (search_figshare, "figshare"),
        (search_dryad, "dryad"),
    ]:
        rows, errs = search_fn(session, queries, repo_per_query, strategy="citation")
        raw_rows.extend(rows)
        errors.extend(errs)
        announce(f"  source-family alias provider complete: {provider_name}")
    rows, errs = search_openalex(session, queries, biblio_per_query, strategy="citation")
    raw_rows.extend(rows)
    errors.extend(errs)
    rows, errs = search_crossref(session, queries, biblio_per_query, strategy="citation")
    raw_rows.extend(rows)
    errors.extend(errs)
    write_manifest(
        SOURCE_FAMILY_EXPANDED_TARGET,
        strategy_id="plot1_corpusdb_known_source_family_alias_expansion",
        strategy="citation",
        providers=["osf", "dataverse", "datacite", "zenodo", "figshare", "dryad", "openalex", "crossref"],
        queries=queries,
        raw_rows=raw_rows,
        errors=errors,
        replace=replace,
    )


def run_alternate_vocab_expanded(
    session: requests.Session,
    per_query: int,
    replace: bool,
    tracks: dict[str, dict[str, Any]],
) -> None:
    if should_skip(ALTERNATE_VOCAB_EXPANDED_TARGET, replace):
        return
    announce("Running alternate-vocabulary expanded search...")
    queries = queries_for("alternate_vocab_expanded", tracks)
    raw_rows: list[dict[str, str]] = []
    errors: list[str] = []
    rows, errs = search_openalex(session, queries, per_query, strategy="domain")
    raw_rows.extend(rows)
    errors.extend(errs)
    rows, errs = search_crossref(session, queries, per_query, strategy="domain")
    raw_rows.extend(rows)
    errors.extend(errs)
    rows, errs = search_europepmc(session, queries, per_query, strategy="domain")
    raw_rows.extend(rows)
    errors.extend(errs)
    rows, errs = search_osf(session, queries, max(1, per_query // 2), strategy="domain")
    raw_rows.extend(rows)
    errors.extend(errs)
    rows, errs = search_dataverse(session, queries, max(1, per_query // 2), strategy="domain")
    raw_rows.extend(rows)
    errors.extend(errs)
    rows, errs = search_datacite(session, queries, max(1, per_query // 2), strategy="domain")
    raw_rows.extend(rows)
    errors.extend(errs)
    write_manifest(
        ALTERNATE_VOCAB_EXPANDED_TARGET,
        strategy_id="plot1_corpusdb_alternate_vocabulary_expanded_search",
        strategy="domain",
        providers=["openalex", "crossref", "europepmc", "osf", "dataverse", "datacite"],
        queries=queries,
        raw_rows=raw_rows,
        errors=errors,
        replace=replace,
    )


def run_link_graph(session: requests.Session, per_query: int, replace: bool, tracks: dict[str, dict[str, Any]]) -> None:
    if should_skip(LINK_GRAPH_TARGET, replace):
        return
    announce("Running publication-data link graph search...")
    seed_dois = seed_dois_from_existing(max_extra=max(5, per_query * 4))
    queries = queries_for("link_graph", tracks)
    for query in queries:
        doi = normalize_doi(query)
        if doi and doi not in seed_dois:
            seed_dois.append(doi)
    seed_dois = seed_dois[: max(5, int(os.environ.get("FIGURE1_LINK_GRAPH_MAX_SEEDS", "24")))]
    raw_rows: list[dict[str, str]] = []
    errors: list[str] = []
    rows, errs = search_datacite_related(session, seed_dois, max(1, min(per_query, 6)))
    raw_rows.extend(rows)
    errors.extend(errs)
    rows, errs = search_scholexplorer_links(session, seed_dois, max(1, min(per_query, 6)))
    raw_rows.extend(rows)
    errors.extend(errs)
    rows, errs = search_semantic_scholar_neighbors(session, seed_dois, max(1, min(per_query, 4)))
    raw_rows.extend(rows)
    errors.extend(errs)
    write_manifest(
        LINK_GRAPH_TARGET,
        strategy_id="plot1_corpusdb_publication_data_link_graph_search",
        strategy="link_graph",
        providers=["datacite_related", "openaire_scholexplorer", "semantic_scholar"],
        queries=seed_dois,
        raw_rows=raw_rows,
        errors=errors,
        replace=replace,
    )


def run_gpt_coverage_expanded(
    session: requests.Session,
    per_query: int,
    replace: bool,
    tracks: dict[str, dict[str, Any]],
) -> None:
    if should_skip(GPT_COVERAGE_TARGET, replace):
        return
    announce("Running GPT coverage source-family search...")
    queries = queries_for("gpt_coverage_expanded", tracks)
    raw_rows: list[dict[str, str]] = []
    errors: list[str] = []
    public_per_query = max(1, min(per_query, 3))
    repo_per_query = max(1, min(per_query, 2))
    for search_fn, provider_name, provider_per_query in [
        (search_openalex, "openalex", public_per_query),
        (search_crossref, "crossref", public_per_query),
        (search_europepmc, "europepmc", public_per_query),
        (search_osf, "osf", repo_per_query),
        (search_dataverse, "dataverse", repo_per_query),
        (search_datacite, "datacite", repo_per_query),
        (search_zenodo, "zenodo", repo_per_query),
        (search_figshare, "figshare", repo_per_query),
        (search_dryad, "dryad", repo_per_query),
    ]:
        rows, errs = search_fn(session, queries, provider_per_query, strategy="citation")
        raw_rows.extend(rows)
        errors.extend(errs)
        announce(f"  GPT coverage provider complete: {provider_name}")
    write_manifest(
        GPT_COVERAGE_TARGET,
        strategy_id="plot1_corpusdb_gpt_coverage_source_family_search",
        strategy="citation",
        providers=["openalex", "crossref", "europepmc", "osf", "dataverse", "datacite", "zenodo", "figshare", "dryad"],
        queries=queries,
        raw_rows=raw_rows,
        errors=errors,
        replace=replace,
    )


def run_known_good_recall_probe(
    session: requests.Session,
    per_query: int,
    replace: bool,
    tracks: dict[str, dict[str, Any]],
) -> None:
    del tracks
    if should_skip(KNOWN_GOOD_RECALL_TARGET, replace):
        return
    announce("Running known-good Figure 1 recall probe...")
    queries = known_good_recall_queries()
    raw_rows: list[dict[str, str]] = []
    errors: list[str] = []
    provider_per_query = max(1, min(per_query, 2))
    providers: list[tuple[Any, str]] = [
        (search_openalex, "openalex"),
        (search_crossref, "crossref"),
        (search_europepmc, "europepmc"),
        (search_osf, "osf"),
        (search_dataverse, "dataverse"),
        (search_datacite, "datacite"),
        (search_figshare, "figshare"),
    ]
    if os.environ.get("FIGURE1_KNOWN_GOOD_RECALL_INCLUDE_SLOW_REPOSITORIES") == "1":
        providers.extend([(search_zenodo, "zenodo"), (search_dryad, "dryad")])
    for search_fn, provider_name in providers:
        provider_queries = queries
        if provider_name == "osf":
            # OSF search rejects raw DOI queries containing slashes; DOI hits
            # are still covered by bibliographic/DataCite-style providers.
            provider_queries = [query for query in queries if not DOI_RE.search(query)]
        rows, errs = search_fn(session, provider_queries, provider_per_query, strategy="citation")
        raw_rows.extend(rows)
        errors.extend(errs)
        announce(f"  known-good recall provider complete: {provider_name}")
    write_manifest(
        KNOWN_GOOD_RECALL_TARGET,
        strategy_id="plot1_corpusdb_known_good_recall_probe",
        strategy="citation",
        providers=[provider_name for _, provider_name in providers],
        queries=queries,
        raw_rows=raw_rows,
        errors=errors,
        replace=replace,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strategy",
        action="append",
        choices=[
            "repository",
            "bibliographic",
            "citation",
            "domain",
            "code",
            "registry",
            "archive",
            "manual",
            "repository_expanded",
            "bibliographic_expanded",
            "citation_expanded",
            "domain_expanded",
            "code_expanded",
            "repository_provider_expanded",
            "source_family_expanded",
            "alternate_vocab_expanded",
            "link_graph",
            "gpt_coverage_expanded",
            "known_good_recall",
            "expanded",
            "all",
        ],
        help="Strategy to run. May be provided more than once. Defaults to all.",
    )
    parser.add_argument("--per-query", type=int, default=8, help="Maximum results per provider/query.")
    parser.add_argument("--replace", action="store_true", help="Replace existing target manifests.")
    args = parser.parse_args()

    requested = args.strategy or ["all"]
    all_strategies = ["repository", "bibliographic", "citation", "domain", "code", "registry", "archive", "manual"]
    expanded_strategies = [
        "repository_expanded",
        "bibliographic_expanded",
        "citation_expanded",
        "domain_expanded",
        "code_expanded",
        "repository_provider_expanded",
        "source_family_expanded",
        "alternate_vocab_expanded",
        "link_graph",
        "gpt_coverage_expanded",
        "known_good_recall",
    ]
    strategies: list[str] = []
    if "all" in requested:
        strategies.extend(all_strategies)
    if "expanded" in requested:
        strategies.extend(expanded_strategies)
    strategies.extend(strategy for strategy in requested if strategy not in {"all", "expanded"})
    strategies = list(dict.fromkeys(strategies))
    replace = args.replace or os.environ.get("REPLACE_SEARCH_TARGETS") == "1"
    tracks = load_search_tracks()
    session = make_session()
    if "repository" in strategies:
        run_repository(session, args.per_query, replace, tracks)
    if "bibliographic" in strategies:
        run_bibliographic(session, args.per_query, replace, tracks)
    if "citation" in strategies:
        run_citation(session, args.per_query, replace, tracks)
    if "domain" in strategies:
        run_domain(session, args.per_query, replace, tracks)
    if "code" in strategies:
        run_code(args.per_query, replace, tracks)
    if "registry" in strategies:
        run_registry(session, args.per_query, replace, tracks)
    if "archive" in strategies:
        run_archive(session, args.per_query, replace, tracks)
    if "manual" in strategies:
        run_manual(replace, tracks)
    if "repository_expanded" in strategies:
        run_repository_expanded(session, args.per_query, replace, tracks)
    if "bibliographic_expanded" in strategies:
        run_bibliographic_expanded(session, args.per_query, replace, tracks)
    if "citation_expanded" in strategies:
        run_citation_expanded(session, args.per_query, replace, tracks)
    if "domain_expanded" in strategies:
        run_domain_expanded(session, args.per_query, replace, tracks)
    if "code_expanded" in strategies:
        run_code_expanded(args.per_query, replace, tracks)
    if "repository_provider_expanded" in strategies:
        run_repository_provider_expanded(session, args.per_query, replace, tracks)
    if "source_family_expanded" in strategies:
        run_source_family_expanded(session, args.per_query, replace, tracks)
    if "alternate_vocab_expanded" in strategies:
        run_alternate_vocab_expanded(session, args.per_query, replace, tracks)
    if "link_graph" in strategies:
        run_link_graph(session, args.per_query, replace, tracks)
    if "gpt_coverage_expanded" in strategies:
        run_gpt_coverage_expanded(session, args.per_query, replace, tracks)
    if "known_good_recall" in strategies:
        run_known_good_recall_probe(session, args.per_query, replace, tracks)


if __name__ == "__main__":
    main()
