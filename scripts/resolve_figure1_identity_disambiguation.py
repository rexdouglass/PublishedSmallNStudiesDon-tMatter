#!/usr/bin/env python3
"""Resolve Figure 1 title-only/weak identities against local source artifacts.

This stage intentionally writes proposals/crosswalks only. It does not edit the
root pair table, source-result tables, or bibliography. The point is to finish
the automatable part of identity grounding before individual replication papers
are chased one by one.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PAIR_CHASE_DIR = ROOT / "steps" / "individual_replication_papers" / "figure1" / "pair_chase"
DEFAULT_WORKLIST = PAIR_CHASE_DIR / "figure1-identity-disambiguation-worklist.tsv"
DEFAULT_OUTPUT_DIR = PAIR_CHASE_DIR

PAPER_REFS = ROOT / "data" / "derived" / "bibliography" / "paper_references.csv"
CORPUS_REFS = ROOT / "data" / "derived" / "bibliography" / "corpus_papers.csv"
RPCB_PAPER_LEVEL = ROOT / "data" / "raw" / "corpus_candidates" / "rpcb" / "RP_CB Final Analysis - Paper level data.csv"
SCORE_CASES = ROOT / "data" / "raw" / "source_artifacts" / "figure1" / "score" / "source_artifact_c15b7ff6b69d45bb__repli_all_cases.csv"
SCORE_STATUS = ROOT / "data" / "raw" / "source_artifacts" / "figure1" / "score" / "source_artifact_f1587bcc89a39a90__score_rr-project_status.csv"
SCORE_METADATA = ROOT / "data" / "raw" / "source_artifacts" / "figure1" / "score" / "source_artifact_ceb9c9ce701aec16__paper_metadata.csv"
SCORE_CITATIONS = ROOT / "data" / "raw" / "source_artifacts" / "figure1" / "score" / "source_artifact_c98d50489261c329__paper_citations.csv"
REPEAT_PROMOTED = ROOT / "data" / "derived" / "replication_pairs" / "harvest" / "promoted" / "repeat_rwe_reproductions__promoted_pairs.csv"

RESOLUTION_COLUMNS = [
    "identity_disambiguation_task_id",
    "figure1_individual_study_id",
    "primary_bibtex_key",
    "study_dedupe_key",
    "study_dedupe_method",
    "identity_disambiguation_priority",
    "roles_observed",
    "source_family_keys",
    "represented_title_canonical",
    "represented_doi_canonical",
    "represented_url_canonical",
    "n_side_targets",
    "n_distinct_pairs",
    "n_included_pairs",
    "n_excluded_pairs",
    "resolution_status",
    "resolution_confidence",
    "resolution_basis",
    "resolved_title",
    "resolved_authors",
    "resolved_year",
    "resolved_venue",
    "resolved_doi",
    "resolved_pmid",
    "resolved_pmcid",
    "resolved_url",
    "resolved_source_type",
    "resolution_source_artifact",
    "resolution_source_locator",
    "verbatim_match_evidence",
    "match_score",
    "match_candidate_key",
    "match_candidate_source_rows",
    "recommended_update_action",
    "next_action",
    "figure1_replication_pair_ids_json",
    "side_target_ids_json",
    "resolved_at",
]

DOI_RE = re.compile(r"(10\.\d{4,9}/[^\s\"<>]+)", re.IGNORECASE)
SCORE_RE = re.compile(r"\(SCORE\s+([^)]+)\)", re.IGNORECASE)
RPCB_RE = re.compile(r"paper[_\s-]*(\d+)(?:[_\s-]+experiment[_\s-]*(\d+))?", re.IGNORECASE)
REPEAT_ORIG_RE = re.compile(r"REPEAT original healthcare database study\s+(\d+)", re.IGNORECASE)
AUTHOR_YEAR_RE = re.compile(r"\(([^()]*?),\s*(\d{4})[a-z]?\)")
CITATION_TITLE_RE = re.compile(r"\(\s*(\d{4})\s*\)\.?\s+(.+?)(?:\.\s+[A-Z][A-Za-z &-]+|\.\s*$)")


def clean(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    text = str(value).strip()
    if text.lower() in {"nan", "none", "null", "<na>"}:
        return ""
    return text


def norm_doi(value: Any) -> str:
    text = clean(value)
    if not text:
        return ""
    match = DOI_RE.search(text)
    if match:
        text = match.group(1)
    text = text.strip().rstrip(".,);]")
    return text.lower()


def norm_text(value: Any) -> str:
    text = unicodedata.normalize("NFKD", clean(value))
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = text.replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def tokens(value: str) -> set[str]:
    stop = {
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
    return {token for token in norm_text(value).split() if token and token not in stop}


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    sep = "\t" if path.suffix.lower() == ".tsv" else ","
    return pd.read_csv(path, sep=sep, dtype=str, keep_default_na=False)


def best_ref_rows(refs: pd.DataFrame) -> pd.DataFrame:
    refs = refs.copy()
    refs["doi_norm"] = refs["doi"].map(norm_doi)
    refs["title_norm"] = refs["title"].map(norm_text)
    refs["score_priority"] = 0
    refs.loc[refs["doi_norm"] != "", "score_priority"] += 10
    refs.loc[refs["pmid"].map(clean) != "", "score_priority"] += 3
    refs.loc[refs["pmcid"].map(clean) != "", "score_priority"] += 3
    refs.loc[refs["url"].map(clean) != "", "score_priority"] += 1
    refs.loc[refs["metadata_source"].isin(["manual", "crossref"]), "score_priority"] += 4
    refs.loc[refs["ref_table"].eq("paper_references"), "score_priority"] += 2
    refs = refs.sort_values(["score_priority", "key"], ascending=[False, True])
    return refs


def load_refs() -> tuple[pd.DataFrame, dict[str, dict[str, str]], dict[str, list[dict[str, str]]], dict[str, list[dict[str, str]]]]:
    parts = []
    if PAPER_REFS.exists():
        parts.append(read_csv(PAPER_REFS).assign(ref_table="paper_references"))
    if CORPUS_REFS.exists():
        parts.append(read_csv(CORPUS_REFS).assign(ref_table="corpus_papers"))
    if not parts:
        empty = pd.DataFrame(columns=["key", "title", "authors", "year", "journal", "doi", "url", "pmid", "pmcid"])
        return empty, {}, {}, {}
    refs = pd.concat(parts, ignore_index=True)
    for col in ["key", "title", "authors", "year", "journal", "doi", "url", "pmid", "pmcid", "metadata_source", "source_rows"]:
        if col not in refs.columns:
            refs[col] = ""
    refs = best_ref_rows(refs)
    by_title: dict[str, dict[str, str]] = {}
    by_year: dict[str, list[dict[str, str]]] = defaultdict(list)
    by_doi: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in refs.to_dict("records"):
        row = {key: clean(value) for key, value in row.items()}
        title_norm = clean(row.get("title_norm"))
        if title_norm and title_norm not in by_title:
            by_title[title_norm] = row
        year = clean(row.get("year"))
        if year:
            by_year[year].append(row)
        doi = norm_doi(row.get("doi"))
        if doi:
            by_doi[doi].append(row)
    return refs, by_title, by_year, by_doi


def ref_resolution(row: dict[str, str], basis: str, confidence: str, source_artifact: str, locator: str, evidence: str, score: str = "1.0") -> dict[str, str]:
    doi = norm_doi(row.get("doi"))
    resolved_url = clean(row.get("url")) or (f"https://doi.org/{doi}" if doi else "")
    has_external_id = bool(doi or clean(row.get("pmid")) or clean(row.get("pmcid")) or resolved_url)
    status = "resolved" if has_external_id else "retained_local_identity"
    action = (
        "propose_resolved_citation_for_identity; preserve original local label in provenance fields"
        if has_external_id
        else "retain_as_local_no_repull_dedupe_identity; external DOI/PMID/PMCID/stable URL still needed before level4"
    )
    return {
        "resolution_status": status,
        "resolution_confidence": confidence,
        "resolution_basis": basis,
        "resolved_title": clean(row.get("title")),
        "resolved_authors": clean(row.get("authors")),
        "resolved_year": clean(row.get("year")),
        "resolved_venue": clean(row.get("journal")),
        "resolved_doi": doi,
        "resolved_pmid": clean(row.get("pmid")),
        "resolved_pmcid": clean(row.get("pmcid")),
        "resolved_url": resolved_url,
        "resolved_source_type": "bibliographic_record",
        "resolution_source_artifact": source_artifact,
        "resolution_source_locator": locator,
        "verbatim_match_evidence": evidence,
        "match_score": score,
        "match_candidate_key": clean(row.get("key")),
        "match_candidate_source_rows": clean(row.get("source_rows")),
        "recommended_update_action": action,
    }


def unresolved(reason: str, next_action: str = "manual_identity_review_or_source_family_backfill") -> dict[str, str]:
    return {
        "resolution_status": "unresolved",
        "resolution_confidence": "low",
        "resolution_basis": reason,
        "resolved_title": "",
        "resolved_authors": "",
        "resolved_year": "",
        "resolved_venue": "",
        "resolved_doi": "",
        "resolved_pmid": "",
        "resolved_pmcid": "",
        "resolved_url": "",
        "resolved_source_type": "",
        "resolution_source_artifact": "",
        "resolution_source_locator": "",
        "verbatim_match_evidence": "",
        "match_score": "0",
        "match_candidate_key": "",
        "match_candidate_source_rows": "",
        "recommended_update_action": next_action,
    }


def stable_url_resolution(title: str, url: str, basis: str, confidence: str = "medium") -> dict[str, str]:
    doi = norm_doi(url)
    return {
        "resolution_status": "resolved",
        "resolution_confidence": confidence,
        "resolution_basis": basis,
        "resolved_title": title,
        "resolved_authors": "",
        "resolved_year": "",
        "resolved_venue": "",
        "resolved_doi": doi,
        "resolved_pmid": "",
        "resolved_pmcid": "",
        "resolved_url": f"https://doi.org/{doi}" if doi else url,
        "resolved_source_type": "stable_url_or_doi_from_task",
        "resolution_source_artifact": "steps/individual_replication_papers/figure1/pair_chase/figure1-identity-disambiguation-worklist.tsv",
        "resolution_source_locator": "represented_url_canonical|represented_doi_canonical",
        "verbatim_match_evidence": url,
        "match_score": "1.0" if doi else "0.75",
        "match_candidate_key": "",
        "match_candidate_source_rows": "",
        "recommended_update_action": "treat_task_identity_as_grounded_by_existing_doi_or_stable_url; preserve local label",
    }


def build_canonical_records(refs_by_title: dict[str, dict[str, str]]) -> dict[str, dict[str, str]]:
    specs = {
        "rpp_2015": "Estimating the reproducibility of psychological science",
        "osc_2015": "Estimating the reproducibility of psychological science",
        "many_labs_2": "Many Labs 2: Investigating Variation in Replicability Across Samples and Settings",
        "many_labs_5": "Many Labs 5: Testing pre-data collection peer review as an intervention to increase replicability",
        "many_labs_1": "Investigating variation in replicability: A Many Labs replication project",
        "many_labs_3": "Many Labs 3: Evaluating participant pool quality across the academic semester via replication",
        "ssrp_camerer_2018": "Evaluating the replicability of social science experiments in Nature and Science between 2010 and 2015",
        "pipeline_project_2016": "The pipeline project: Pre-publication independent replications of a single laboratory's research pipeline",
        "cova_xphi_2018": "Estimating the reproducibility of experimental philosophy",
        "repeat_wang_2022": "Empirical evaluation of the reproducibility of real-world evidence studies using clinical practice data",
        "rpcb_summary_2021": "Investigating the replicability of preclinical cancer biology",
    }
    out = {}
    for key, title in specs.items():
        row = refs_by_title.get(norm_text(title))
        if row:
            out[key] = row
    return out


def resolve_rpcb(task: dict[str, str], refs_by_title: dict[str, dict[str, str]], rpcb: pd.DataFrame) -> dict[str, str] | None:
    title = clean(task.get("represented_title_canonical"))
    match = RPCB_RE.search(title)
    if not match or rpcb.empty:
        return None
    paper_no = match.group(1)
    exp_no = match.group(2) or ""
    paper_rows = rpcb[rpcb["Paper #"].map(clean) == paper_no]
    if paper_rows.empty:
        return unresolved("rpcb_paper_number_not_found", "manual_rpcb_paper_number_review")
    raw = {key: clean(value) for key, value in paper_rows.iloc[0].to_dict().items()}
    resolved_title = clean(raw.get("Original paper title"))
    ref = refs_by_title.get(norm_text(resolved_title))
    locator = f"Paper #={paper_no}" + (f"; Experiment #={exp_no}" if exp_no else "")
    evidence = f"Paper # {paper_no}: {resolved_title}; journal={clean(raw.get('Original paper journal'))}; year={clean(raw.get('Year'))}"
    if ref and norm_doi(ref.get("doi")):
        return ref_resolution(
            ref,
            "rpcb_paper_number_to_paper_level_metadata_then_local_bibliography_doi",
            "high",
            rel(RPCB_PAPER_LEVEL),
            locator,
            evidence,
            "0.97",
        )
    return {
        "resolution_status": "resolved",
        "resolution_confidence": "medium",
        "resolution_basis": "rpcb_paper_number_to_paper_level_metadata_no_local_doi",
        "resolved_title": resolved_title,
        "resolved_authors": "",
        "resolved_year": clean(raw.get("Year")),
        "resolved_venue": clean(raw.get("Original paper journal")),
        "resolved_doi": "",
        "resolved_pmid": "",
        "resolved_pmcid": "",
        "resolved_url": clean(raw.get("OSF project link")) or clean(raw.get("Link to Replication study")) or clean(raw.get("Link to Registered Report")),
        "resolved_source_type": "source_family_paper_metadata",
        "resolution_source_artifact": rel(RPCB_PAPER_LEVEL),
        "resolution_source_locator": locator,
        "verbatim_match_evidence": evidence,
        "match_score": "0.8",
        "match_candidate_key": "",
        "match_candidate_source_rows": "",
        "recommended_update_action": "propose_rpcb_original_paper_title_year_journal; DOI still needs grounding if used for level4",
    }


def load_score_tables() -> dict[str, pd.DataFrame]:
    return {
        "cases": read_csv(SCORE_CASES),
        "status": read_csv(SCORE_STATUS),
        "metadata": read_csv(SCORE_METADATA),
        "citations": read_csv(SCORE_CITATIONS),
    }


def resolve_score(task: dict[str, str], score: dict[str, pd.DataFrame]) -> dict[str, str] | None:
    title = clean(task.get("represented_title_canonical"))
    source_family = clean(task.get("source_family_keys"))
    if "score" not in source_family.lower():
        return None
    match = SCORE_RE.search(title)
    if not match:
        return None
    report_id = match.group(1).strip()
    cases = score.get("cases", pd.DataFrame())
    status = score.get("status", pd.DataFrame())
    metadata = score.get("metadata", pd.DataFrame())
    citations = score.get("citations", pd.DataFrame())
    if cases.empty:
        return unresolved("score_cases_table_missing", "manual_score_report_id_review")
    case_rows = cases[cases["report_id"].map(clean) == report_id]
    if case_rows.empty:
        return unresolved("score_report_id_not_found", "manual_score_report_id_review")
    case = {key: clean(value) for key, value in case_rows.iloc[0].to_dict().items()}
    paper_id = case.get("paper_id", "")
    rr_id = case.get("rr_id", "")
    role = clean(task.get("roles_observed")).lower()

    meta = {}
    if not metadata.empty and paper_id:
        m = metadata[metadata["paper_id"].map(clean) == paper_id]
        if not m.empty:
            meta = {key: clean(value) for key, value in m.iloc[0].to_dict().items()}
    cite = {}
    if not citations.empty and paper_id:
        c = citations[citations["paper_id"].map(clean) == paper_id]
        if not c.empty:
            cite = {key: clean(value) for key, value in c.iloc[0].to_dict().items()}
    stat = {}
    if not status.empty and rr_id:
        s = status[status["rr_id"].map(clean) == rr_id]
        if not s.empty:
            stat = {key: clean(value) for key, value in s.iloc[0].to_dict().items()}
    project_guid = stat.get("project_guid", "")
    source_url = f"https://osf.io/{project_guid}/" if project_guid else clean(stat.get("prereg_links"))
    locator = f"report_id={report_id}; rr_id={rr_id}; paper_id={paper_id}"
    if role == "original":
        doi = norm_doi(meta.get("DOI") or cite.get("doi"))
        resolved_title = clean(meta.get("title")) or clean(cite.get("citation")) or title
        evidence = (
            f"{locator}; citation={clean(cite.get('citation'))}; "
            f"title={clean(meta.get('title'))}; DOI={doi}"
        )
        return {
            "resolution_status": "resolved",
            "resolution_confidence": "high" if doi else "medium",
            "resolution_basis": "score_report_id_to_original_paper_metadata",
            "resolved_title": resolved_title,
            "resolved_authors": clean(meta.get("author_first")) + (" " if clean(meta.get("author_first")) and clean(meta.get("author_last")) else "") + clean(meta.get("author_last")),
            "resolved_year": clean(meta.get("pub_year")),
            "resolved_venue": clean(meta.get("publication_standard")),
            "resolved_doi": doi,
            "resolved_pmid": "",
            "resolved_pmcid": "",
            "resolved_url": f"https://doi.org/{doi}" if doi else source_url,
            "resolved_source_type": "score_original_paper_metadata",
            "resolution_source_artifact": f"{rel(SCORE_CASES)}; {rel(SCORE_METADATA)}; {rel(SCORE_CITATIONS)}",
            "resolution_source_locator": locator,
            "verbatim_match_evidence": evidence,
            "match_score": "0.95" if doi else "0.75",
            "match_candidate_key": "",
            "match_candidate_source_rows": "",
            "recommended_update_action": "propose_score_original_paper_citation; preserve SCORE report_id link",
        }
    report_title = f"SCORE replication report {report_id} for {clean(cite.get('citation')) or clean(meta.get('citation')) or paper_id}".strip()
    evidence = f"{locator}; project_guid={project_guid}; prereg_links={clean(stat.get('prereg_links'))}"
    return {
        "resolution_status": "resolved",
        "resolution_confidence": "medium",
        "resolution_basis": "score_report_id_to_replication_report_project",
        "resolved_title": report_title,
        "resolved_authors": "SCORE Collaboration",
        "resolved_year": "",
        "resolved_venue": "SCORE replication report / OSF project",
        "resolved_doi": "",
        "resolved_pmid": "",
        "resolved_pmcid": "",
        "resolved_url": source_url,
        "resolved_source_type": "score_replication_report_project",
        "resolution_source_artifact": f"{rel(SCORE_CASES)}; {rel(SCORE_STATUS)}",
        "resolution_source_locator": locator,
        "verbatim_match_evidence": evidence,
        "match_score": "0.72",
        "match_candidate_key": "",
        "match_candidate_source_rows": "",
        "recommended_update_action": "retain_as_score_report_project_identity; use original paper metadata separately for represented original",
    }


def resolve_repeat(task: dict[str, str], repeat: pd.DataFrame, canon: dict[str, dict[str, str]]) -> dict[str, str] | None:
    title = clean(task.get("represented_title_canonical"))
    source_family = clean(task.get("source_family_keys")).lower()
    if "repeat" not in source_family and "REPEAT" not in title:
        return None
    if "wang et al. 2022 repeat reproduction" in title.lower() and "repeat_wang_2022" in canon:
        return ref_resolution(
            canon["repeat_wang_2022"],
            "repeat_replication_side_to_wang_2022_publication",
            "high",
            "data/derived/bibliography/paper_references.csv",
            "canonical REPEAT reproduction publication",
            title,
            "0.95",
        )
    match = REPEAT_ORIG_RE.search(title)
    if not match or repeat.empty:
        return None
    study_id = int(match.group(1))
    rows = repeat[repeat["match_author"].map(clean).str.extract(r"repeat_study_(\d+)", expand=False).fillna("").astype(str).str.lstrip("0").replace({"": "-1"}).astype(int) == study_id]
    if rows.empty:
        rows = repeat[repeat["pair_id"].map(clean).str.contains(f"repeat_study_{study_id:03d}", regex=False)]
    if rows.empty:
        return unresolved("repeat_study_id_not_found_in_promoted_pairs", "manual_repeat_source_data_review")
    raw = {key: clean(value) for key, value in rows.iloc[0].to_dict().items()}
    evidence = (
        f"pair_id={raw.get('pair_id')}; original_title={raw.get('original_title')}; "
        f"outcome={raw.get('outcome')}; raw_file={raw.get('raw_file')}"
    )
    return {
        "resolution_status": "resolved",
        "resolution_confidence": "medium",
        "resolution_basis": "repeat_internal_original_study_id_to_promoted_pair_source_data",
        "resolved_title": raw.get("original_title") or title,
        "resolved_authors": "",
        "resolved_year": "",
        "resolved_venue": "REPEAT Supplementary Data 6",
        "resolved_doi": norm_doi(raw.get("original_doi")),
        "resolved_pmid": "",
        "resolved_pmcid": "",
        "resolved_url": "https://osf.io/my5gn/",
        "resolved_source_type": "source_family_internal_original_study",
        "resolution_source_artifact": rel(REPEAT_PROMOTED),
        "resolution_source_locator": f"studyid={study_id}",
        "verbatim_match_evidence": evidence,
        "match_score": "0.7",
        "match_candidate_key": "",
        "match_candidate_source_rows": "",
        "recommended_update_action": "retain_as_repeat_internal_original_study_unless original PMID/DOI is recovered from Supplementary Data 5",
    }


def resolve_canonical_replication_label(task: dict[str, str], canon: dict[str, dict[str, str]]) -> dict[str, str] | None:
    title = clean(task.get("represented_title_canonical"))
    role = clean(task.get("roles_observed")).lower()
    family = clean(task.get("source_family_keys")).lower()
    norm = norm_text(title)
    key = ""
    if title in {"RPP 2015", "OSC 2015"}:
        key = "rpp_2015"
    elif title == "Cova 2018 xphi":
        key = "cova_xphi_2018"
    elif title == "Pipeline Project 2016" or "pipeline_project" in family and role == "replication":
        key = "pipeline_project_2016"
    elif "SSRP Camerer 2018" in title or "ssrp" in family and role == "replication":
        key = "ssrp_camerer_2018"
    elif title.startswith("Many Labs 2 -") or ("many_labs_2" in family and role == "replication"):
        key = "many_labs_2"
    elif "many_labs_5" in family and role == "replication":
        key = "many_labs_5"
    elif "many labs 1" in norm and role == "replication":
        key = "many_labs_1"
    elif "many labs 3" in norm and role == "replication":
        key = "many_labs_3"
    elif title == "RPCB native effect tables" or ("rpcb" in family and role == "replication"):
        key = "rpcb_summary_2021"
    if not key or key not in canon:
        return None
    return ref_resolution(
        canon[key],
        f"canonical_source_family_replication_label:{key}",
        "high",
        "data/derived/bibliography/paper_references.csv; data/derived/bibliography/corpus_papers.csv",
        title,
        f"local label {title} mapped to canonical source-family publication {clean(canon[key].get('title'))}",
        "0.95",
    )


def resolve_manual_label(task: dict[str, str]) -> dict[str, str] | None:
    title = clean(task.get("represented_title_canonical"))
    manual = {
        "Srull & Wyer hostility priming": {
            "resolved_title": "The Role of Category Accessibility in the Interpretation of Information About Persons: Some Determinants and Implications",
            "resolved_authors": "Srull, Thomas K. and Wyer, Robert S.",
            "resolved_year": "1979",
            "resolved_venue": "Journal of Personality and Social Psychology",
            "resolved_doi": "10.1037/0022-3514.37.10.1660",
            "resolved_url": "https://doi.org/10.1037/0022-3514.37.10.1660",
            "basis": "manual_local_rule_for_known_rrr_original_label",
        },
    }
    if title not in manual:
        return None
    row = manual[title]
    return {
        "resolution_status": "resolved",
        "resolution_confidence": "high",
        "resolution_basis": row["basis"],
        "resolved_title": row["resolved_title"],
        "resolved_authors": row["resolved_authors"],
        "resolved_year": row["resolved_year"],
        "resolved_venue": row["resolved_venue"],
        "resolved_doi": row["resolved_doi"],
        "resolved_pmid": "",
        "resolved_pmcid": "",
        "resolved_url": row["resolved_url"],
        "resolved_source_type": "manual_bibliographic_rule",
        "resolution_source_artifact": "scripts/resolve_figure1_identity_disambiguation.py",
        "resolution_source_locator": title,
        "verbatim_match_evidence": title,
        "match_score": "0.95",
        "match_candidate_key": "",
        "match_candidate_source_rows": "",
        "recommended_update_action": "propose_resolved_citation_for_identity; preserve shorthand local label in provenance fields",
    }


def resolve_exact_title(task: dict[str, str], refs_by_title: dict[str, dict[str, str]]) -> dict[str, str] | None:
    title = clean(task.get("represented_title_canonical"))
    if not title:
        return None
    row = refs_by_title.get(norm_text(title))
    if not row:
        return None
    score = "0.95" if norm_doi(row.get("doi")) else "0.8"
    return ref_resolution(
        row,
        "exact_normalized_title_match_to_local_bibliography",
        "high" if norm_doi(row.get("doi")) else "medium",
        "data/derived/bibliography/paper_references.csv; data/derived/bibliography/corpus_papers.csv",
        "normalized title",
        f"task title={title}; matched title={clean(row.get('title'))}",
        score,
    )


def resolve_citation_title(task: dict[str, str], refs_by_title: dict[str, dict[str, str]]) -> dict[str, str] | None:
    title = clean(task.get("represented_title_canonical"))
    match = CITATION_TITLE_RE.search(title)
    if not match:
        return None
    year = match.group(1)
    extracted = match.group(2).strip()
    row = refs_by_title.get(norm_text(extracted))
    if not row:
        return None
    if clean(row.get("year")) and clean(row.get("year")) != year:
        return None
    return ref_resolution(
        row,
        "citation_string_title_year_to_local_bibliography",
        "high" if norm_doi(row.get("doi")) else "medium",
        "data/derived/bibliography/paper_references.csv; data/derived/bibliography/corpus_papers.csv",
        "parsed citation title/year",
        f"parsed year={year}; parsed title={extracted}; matched title={clean(row.get('title'))}",
        "0.9",
    )


def author_names_from_label(label: str) -> tuple[list[str], str]:
    match = AUTHOR_YEAR_RE.search(label)
    if not match:
        return [], ""
    author_part = match.group(1)
    year = match.group(2)
    author_part = re.sub(r"\bet\s+al\.?", "", author_part, flags=re.IGNORECASE)
    author_part = author_part.replace("&", ",").replace(" and ", ",")
    names = []
    for piece in author_part.split(","):
        name = norm_text(piece).strip()
        if not name:
            continue
        # Keep the last token as a likely family name if initials are present.
        names.append(name.split()[-1])
    return list(dict.fromkeys(names)), year


def resolve_author_year_label(task: dict[str, str], refs_by_year: dict[str, list[dict[str, str]]]) -> dict[str, str] | None:
    title = clean(task.get("represented_title_canonical"))
    names, year = author_names_from_label(title)
    if not names or not year:
        return None
    candidates = []
    label_tokens = tokens(re.sub(r"\([^)]*\)", "", title))
    for ref in refs_by_year.get(year, []):
        author_text = norm_text(clean(ref.get("authors")))
        if not author_text:
            continue
        if not all(name in author_text for name in names):
            continue
        ref_tokens = tokens(clean(ref.get("title")))
        overlap = len(label_tokens & ref_tokens) / max(1, len(label_tokens | ref_tokens)) if label_tokens else 0
        candidates.append((overlap, ref))
    if not candidates:
        return None
    candidates.sort(key=lambda item: (item[0], 1 if norm_doi(item[1].get("doi")) else 0, clean(item[1].get("key"))), reverse=True)
    best_overlap, best = candidates[0]
    if len(candidates) > 1 and best_overlap < 0.35:
        return None
    if len(candidates) > 1 and abs(best_overlap - candidates[1][0]) < 0.05:
        return None
    return ref_resolution(
        best,
        "author_year_label_to_unique_local_bibliography_candidate",
        "medium",
        "data/derived/bibliography/paper_references.csv; data/derived/bibliography/corpus_papers.csv",
        "parsed author-year label",
        f"label={title}; parsed_names={','.join(names)}; year={year}; matched_title={clean(best.get('title'))}",
        f"{0.65 + min(best_overlap, 0.35):.2f}",
    )


def resolve_fuzzy_title(task: dict[str, str], refs: pd.DataFrame) -> dict[str, str] | None:
    title = clean(task.get("represented_title_canonical"))
    title_norm = norm_text(title)
    if len(title_norm) < 25:
        return None
    title_tokens = tokens(title)
    if len(title_tokens) < 4:
        return None
    best: tuple[float, dict[str, str]] | None = None
    # Restrict fuzzy matching to references that have a DOI or URL and a title
    # within a plausible length. This avoids upgrading local labels too eagerly.
    for row in refs.to_dict("records"):
        ref_title = clean(row.get("title"))
        if not ref_title:
            continue
        if not norm_doi(row.get("doi")) and not clean(row.get("url")):
            continue
        ref_norm = clean(row.get("title_norm"))
        if not ref_norm:
            continue
        if title_norm == ref_norm:
            continue
        ref_tokens = tokens(ref_title)
        if not ref_tokens:
            continue
        jaccard = len(title_tokens & ref_tokens) / max(1, len(title_tokens | ref_tokens))
        substring = title_norm in ref_norm or ref_norm in title_norm
        if jaccard >= 0.88 or (substring and jaccard >= 0.65):
            if best is None or jaccard > best[0]:
                best = (jaccard, {key: clean(value) for key, value in row.items()})
    if not best:
        return None
    jaccard, row = best
    return ref_resolution(
        row,
        "conservative_fuzzy_title_match_to_local_bibliography",
        "medium",
        "data/derived/bibliography/paper_references.csv; data/derived/bibliography/corpus_papers.csv",
        "token-jaccard title match",
        f"task title={title}; matched title={clean(row.get('title'))}; token_jaccard={jaccard:.3f}",
        f"{jaccard:.3f}",
    )


def resolve_one(task: dict[str, str], context: dict[str, Any]) -> dict[str, str]:
    title = clean(task.get("represented_title_canonical"))
    doi = norm_doi(task.get("represented_doi_canonical"))
    url = clean(task.get("represented_url_canonical"))
    if doi:
        return stable_url_resolution(title, f"https://doi.org/{doi}", "doi_present_in_identity_worklist", "high")
    if norm_doi(url):
        return stable_url_resolution(title, url, "doi_url_present_in_identity_worklist", "high")
    if url:
        return stable_url_resolution(title, url, "stable_url_present_in_identity_worklist", "medium")

    resolvers = [
        lambda t: resolve_rpcb(t, context["refs_by_title"], context["rpcb"]),
        lambda t: resolve_score(t, context["score"]),
        lambda t: resolve_repeat(t, context["repeat"], context["canon"]),
        lambda t: resolve_canonical_replication_label(t, context["canon"]),
        resolve_manual_label,
        lambda t: resolve_citation_title(t, context["refs_by_title"]),
        lambda t: resolve_author_year_label(t, context["refs_by_year"]),
        lambda t: resolve_exact_title(t, context["refs_by_title"]),
        lambda t: resolve_fuzzy_title(t, context["refs"]),
    ]
    for resolver in resolvers:
        result = resolver(task)
        if result:
            return result
    return unresolved("no_local_resolution_route_matched")


def build_outputs(worklist: pd.DataFrame, output_dir: Path, replace: bool) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "figure1-identity-disambiguation-resolutions.tsv"
    unresolved_path = output_dir / "figure1-identity-disambiguation-unresolved.tsv"
    summary_path = output_dir / "figure1-identity-disambiguation-resolution-summary.md"
    if not replace:
        for path in [out_path, unresolved_path, summary_path]:
            if path.exists():
                raise FileExistsError(f"{path} exists; rerun with --replace")

    refs, refs_by_title, refs_by_year, _refs_by_doi = load_refs()
    context = {
        "refs": refs,
        "refs_by_title": refs_by_title,
        "refs_by_year": refs_by_year,
        "canon": build_canonical_records(refs_by_title),
        "rpcb": read_csv(RPCB_PAPER_LEVEL),
        "score": load_score_tables(),
        "repeat": read_csv(REPEAT_PROMOTED),
    }
    resolved_at = datetime.now(timezone.utc).isoformat()
    rows = []
    for raw in worklist.to_dict("records"):
        task = {key: clean(value) for key, value in raw.items()}
        result = resolve_one(task, context)
        row = {
            "identity_disambiguation_task_id": task.get("identity_disambiguation_task_id", ""),
            "figure1_individual_study_id": task.get("figure1_individual_study_id", ""),
            "primary_bibtex_key": task.get("primary_bibtex_key", ""),
            "study_dedupe_key": task.get("study_dedupe_key", ""),
            "study_dedupe_method": task.get("study_dedupe_method", ""),
            "identity_disambiguation_priority": task.get("identity_disambiguation_priority", ""),
            "roles_observed": task.get("roles_observed", ""),
            "source_family_keys": task.get("source_family_keys", ""),
            "represented_title_canonical": task.get("represented_title_canonical", ""),
            "represented_doi_canonical": task.get("represented_doi_canonical", ""),
            "represented_url_canonical": task.get("represented_url_canonical", ""),
            "n_side_targets": task.get("n_side_targets", ""),
            "n_distinct_pairs": task.get("n_distinct_pairs", ""),
            "n_included_pairs": task.get("n_included_pairs", ""),
            "n_excluded_pairs": task.get("n_excluded_pairs", ""),
            "next_action": task.get("next_action", ""),
            "figure1_replication_pair_ids_json": task.get("figure1_replication_pair_ids_json", ""),
            "side_target_ids_json": task.get("side_target_ids_json", ""),
            "resolved_at": resolved_at,
        }
        row.update(result)
        rows.append({col: clean(row.get(col, "")) for col in RESOLUTION_COLUMNS})

    out = pd.DataFrame(rows, columns=RESOLUTION_COLUMNS)
    unresolved_df = out[out["resolution_status"] != "resolved"].copy()
    out.to_csv(out_path, sep="\t", index=False)
    unresolved_df.to_csv(unresolved_path, sep="\t", index=False)

    total = len(out)
    resolved = int((out["resolution_status"] == "resolved").sum())
    retained_local = int((out["resolution_status"] == "retained_local_identity").sum())
    unresolved_n = int((out["resolution_status"] == "unresolved").sum())
    not_external = total - resolved
    included_resolved = int(((out["resolution_status"] == "resolved") & (out["n_included_pairs"].astype(str).replace("", "0").astype(float) > 0)).sum())
    included_total = int((out["n_included_pairs"].astype(str).replace("", "0").astype(float) > 0).sum())
    status_counts = Counter(out["resolution_status"])
    basis_counts = Counter(out[out["resolution_status"] == "resolved"]["resolution_basis"])
    priority_counts = out.groupby(["identity_disambiguation_priority", "resolution_status"]).size().reset_index(name="n")
    family_counts = out.groupby(["source_family_keys", "resolution_status"]).size().reset_index(name="n")

    lines = [
        "# Figure 1 Identity Disambiguation Resolution Summary",
        "",
        f"- Worklist tasks checked: {total:,}",
        f"- Resolved to an external/stable route: {resolved:,}",
        f"- Retained only as local no-repull identities: {retained_local:,}",
        f"- Still unmatched by local rules: {unresolved_n:,}",
        f"- Not externally resolved yet: {not_external:,}",
        f"- Included-pair identities externally resolved: {included_resolved:,} / {included_total:,}",
        "",
        "## Status Counts",
        "",
    ]
    for key, value in status_counts.most_common():
        lines.append(f"- {key}: {value:,}")
    lines.extend(["", "## Top Resolution Bases", ""])
    for key, value in basis_counts.most_common(25):
        lines.append(f"- {key}: {value:,}")
    lines.extend(["", "## Priority x Status", ""])
    for raw in priority_counts.to_dict("records"):
        lines.append(f"- {raw['identity_disambiguation_priority']} / {raw['resolution_status']}: {int(raw['n']):,}")
    lines.extend(["", "## Largest Not Externally Resolved Families", ""])
    unresolved_families = family_counts[family_counts["resolution_status"] != "resolved"].sort_values("n", ascending=False)
    for raw in unresolved_families.head(25).to_dict("records"):
        lines.append(f"- {raw['source_family_keys']}: {int(raw['n']):,}")
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- `{rel(out_path)}`",
            f"- `{rel(unresolved_path)}`",
            "",
            "These are citation-resolution proposals. They are not root table edits and should be promoted only through the provenance/schema lanes.",
        ]
    )
    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out_path} ({total} rows; {resolved} externally/stably resolved)")
    print(f"Wrote {unresolved_path} ({len(unresolved_df)} rows not externally resolved; {unresolved_n} unmatched)")
    print(f"Wrote {summary_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worklist", type=Path, default=DEFAULT_WORKLIST)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()
    worklist = read_csv(args.worklist)
    if worklist.empty:
        raise SystemExit(f"No rows found in {args.worklist}")
    build_outputs(worklist, args.output_dir, args.replace)


if __name__ == "__main__":
    main()
