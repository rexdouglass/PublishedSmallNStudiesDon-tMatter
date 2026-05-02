#!/usr/bin/env python3
"""Resolve the sampled provenance pilot back to real-world source handles.

This pass does not claim that every plotted number is verified against the
original paper. It separates three questions:

1. What local file did the plotted value come from?
2. Can that row be linked to a real-world DOI/PMID/PMCID/NCT/URL?
3. Does the literal number come from original-source text, an external corpus,
   or an internal derived table that still needs deeper backfill?
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from difflib import SequenceMatcher
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "data" / "derived" / "effect_inflation_dataset" / "schema_pilot"
CACHE = ROOT / "data" / "cache" / "real_world_grounding"
CROSSREF_CACHE = CACHE / "crossref"
EUROPEPMC_CACHE = CACHE / "europepmc"
SAMPLE_N = int(os.environ.get("SCHEMA_PILOT_N", "300"))
SAMPLE_SUFFIX = f"sample_{SAMPLE_N}"

SOURCE_RESULT = PILOT / f"source_result_codebook_{SAMPLE_SUFFIX}.tsv"
HUMAN_CHECK = PILOT / f"human_check_source_result_{SAMPLE_SUFFIX}.tsv"
REFERENCES = ROOT / "docs" / "references.bib"
OUT_ROWS = PILOT / f"real_world_grounding_{SAMPLE_SUFFIX}.tsv"
OUT_TODOS = PILOT / f"real_world_grounding_todos_{SAMPLE_SUFFIX}.tsv"
OUT_SUMMARY = PILOT / "real_world_grounding_summary.tsv"
OUT_REPORT = PILOT / "real_world_grounding_report.md"
OUT_BELOW_LEVEL3 = PILOT / f"real_world_grounding_below_level3_{SAMPLE_SUFFIX}.tsv"

USER_AGENT = "PublishedSmallNStudies provenance resolver (local audit; contact unavailable)"

DOI_RE = re.compile(r"\b10\.\d{4,9}/[^\s\"<>|]+", re.I)
URL_RE = re.compile(r"https?://[^\s\"<>]+", re.I)
NCT_RE = re.compile(r"\bNCT\d{8}\b", re.I)
PMCID_RE = re.compile(r"\bPMC\d+\b", re.I)
PMID_RE = re.compile(r"\bPMID[:_\s-]*(\d{4,10})\b|\bpubmed[_\s-]*(?:id)?[:_\s-]*(\d{4,10})\b", re.I)
PMCID_LABEL_RE = re.compile(r"\bPMCID[:_\s-]*(?:PMC)?(\d+)\b", re.I)
AEA_TRIAL_RE = re.compile(r"\b(?:AEA\s*RCT\s*Registry\s*trial|AEARCTR)[\s:#-]*(\d{3,7})\b", re.I)
PLOS_ARTICLE_RE = re.compile(r"\bpone\.(\d{6,8})\b", re.I)
DATAVERSE_DVN_RE = re.compile(r"(?:dataverse/|doi:10\.7910/DVN/)([A-Z0-9]{5,8})", re.I)
METABUS_ID_RE = re.compile(r"\b(JAP|PP)-(\d+)-(\d+)-(\d+)\b", re.I)

JOURNAL_FOR_CODE = {
    "JAP": "Journal of Applied Psychology",
    "PP": "Personnel Psychology",
}

SOURCE_FAMILY_URLS = {
    "ClinicalTrials.gov": "https://clinicaltrials.gov/",
    "gwas_catalog": "https://www.ebi.ac.uk/gwas/",
    "GWAS Catalog": "https://www.ebi.ac.uk/gwas/",
    "metaBUS": "https://metabus.org/",
    "metabus": "https://metabus.org/",
    "DARPA SCORE": "https://www.cos.io/score",
    "SCORE": "https://www.cos.io/score",
    "FReD": "https://forrt.org/fred/",
    "RPP": "https://osf.io/ezcuj/",
    "RPCB": "https://osf.io/e5nvr/",
    "MetaLab": "https://metalab.stanford.edu/",
}

SOURCE_SPECIFIC_RESOLUTIONS = {
    "Incidental Disfluency (Alter et al., 2007)": {
        "doi": "10.1037/0096-3445.136.4.569",
        "title": "Overcoming intuition: Metacognitive difficulty activates analytic reasoning.",
        "method": "many_labs_2_original_title_manual_crossref",
        "note": "Many Labs 2 labels this original effect as Incidental Disfluency (Alter et al., 2007); Crossref resolves the matching Alter/Oppenheimer/Epley/Eyre article.",
    },
    "critcher2013": {
        "doi": "10.1037/a0030836",
        "title": "Predicting persons' versus a person's goodness: Behavioral forecasts diverge for individuals versus populations.",
        "method": "boyce_target_lastauthor_year_manual_crossref",
        "note": "Boyce student-replication corpus gives only target_lastauthor_year=critcher2013; Crossref resolves the matching Critcher article.",
    },
    "Etminan": {
        "doi": "10.1038/jcbfm.2011.7",
        "title": "Effect of pharmaceutical treatment on vasospasm, delayed cerebral ischemia, and clinical outcome in patients with aneurysmal subarachnoid hemorrhage: a systematic review and meta-analysis.",
        "method": "button_nord_local_pmc_reference_lookup",
        "note": "Button/Nord workbook gives meta-analysis=Etminan; the mirrored PMC article reference list links Etminan et al. to this DOI.",
    },
    "livingston2012": {
        "doi": "10.1177/0956797611428079",
        "title": "Can an Agentic Black Woman Get Ahead? The Impact of Race and Interpersonal Dominance on Perceptions of Female Leaders",
        "method": "boyce_target_lastauthor_year_manual_crossref",
        "note": "Boyce student-replication corpus gives target_lastauthor_year=livingston2012; exact statistic search and Crossref resolve the Livingston/Rosette/Washington article.",
    },
    "hughes2013": {
        "doi": "10.1177/0956797613494853",
        "title": "Aging 5 Years in 5 Minutes: The Effect of Taking a Memory Test on Older Adults' Subjective Age",
        "method": "boyce_target_lastauthor_year_manual_crossref",
        "note": "Boyce student-replication corpus gives target_lastauthor_year=hughes2013; exact statistic search and PubMed/Crossref resolve the Hughes/Geraci/De Forrest article.",
    },
    "sloman2016_1": {
        "doi": "10.1177/0956797616662271",
        "title": "Your Understanding Is My Understanding",
        "method": "boyce_target_lastauthor_year_manual_crossref",
        "note": "Boyce student-replication corpus gives target_lastauthor_year=sloman2016_1; exact-result search and Crossref resolve the Sloman/Rabb article.",
    },
    "sloman2016_2": {
        "doi": "10.1177/0956797616662271",
        "title": "Your Understanding Is My Understanding",
        "method": "boyce_target_lastauthor_year_manual_crossref",
        "note": "Boyce student-replication corpus gives target_lastauthor_year=sloman2016_2; exact-result search and Crossref resolve the Sloman/Rabb article.",
    },
    "Golden/Gulzar/Sonnet responsiveness - paper median of 5 preregistered result rows": {
        "doi": "10.1177/00104140251381745",
        "title": "Political Responsiveness, Information Provision, and Capacity Gaps",
        "method": "political_science_unlock_manual_crossref",
        "note": "Political-science unlock row gives Golden/Gulzar/Sonnet responsiveness label; Crossref resolves the Comparative Political Studies article.",
    },
}


def safe_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    return re.sub(r"\s+", " ", str(value).replace("\t", " ").replace("\r", " ").replace("\n", " ")).strip()


def read_tsv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False)


def one_line_frame(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for column in out.columns:
        if pd.api.types.is_object_dtype(out[column]) or pd.api.types.is_string_dtype(out[column]):
            out[column] = out[column].map(safe_text)
    return out


def stable_hash(*parts: object, length: int = 16) -> str:
    payload = "\n".join(safe_text(part) for part in parts)
    return hashlib.sha1(payload.encode("utf-8", errors="ignore")).hexdigest()[:length]


def clean_doi(value: str) -> str:
    text = value.strip()
    text = re.sub(r"^(doi:|https?://(?:dx\.)?doi\.org/)", "", text, flags=re.I)
    text = text.replace("\\_", "_")
    text = text.strip().rstrip(".,;)]}'\"")
    return text


def unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        text = safe_text(item)
        if not text:
            continue
        key = text.lower()
        if key not in seen:
            seen.add(key)
            out.append(text)
    return out


def normalize_title(text: str) -> str:
    normalized = safe_text(text).lower()
    normalized = normalized.replace("ñ", "-").replace("–", "-").replace("—", "-")
    normalized = re.sub(r"&amp;", " and ", normalized)
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def title_words(text: str) -> set[str]:
    return {word for word in normalize_title(text).split() if len(word) >= 3}


def citation_title_guess(text: str) -> str:
    """Pull an article-title-looking segment out of a full citation string."""
    raw = safe_text(text)
    if not raw:
        return ""
    raw = re.sub(r"\s+-\s+\d+\s+matched\s+prereg\s+result\(s\)\s*$", "", raw, flags=re.I)
    raw = re.sub(r"^plot\d+::", "", raw, flags=re.I)
    if re.fullmatch(r"[A-Za-z]+_\d+(?:_\d+)?", raw):
        return ""
    if re.fullmatch(r"[A-Za-z]+_\d+", raw):
        return ""
    candidate = raw
    year_match = re.search(r"\(\s*(?:19|20)\d{2}[a-z]?\s*\)\.\s*(.+)$", candidate)
    if year_match:
        candidate = year_match.group(1)
    # Most corpus rows are "Title. Journal, volume, pages". Keep the title.
    journal_start = re.search(
        r"\.\s+(?:Journal|Psychological Science|Developmental Psychology|Personality and Social Psychology Bulletin|"
        r"Personality and Social Psychology Review|Proceedings|Science|Nature|Cognition|Cell|eLife)\b",
        candidate,
        flags=re.I,
    )
    if journal_start:
        candidate = candidate[: journal_start.start()]
    candidate = re.sub(r"\s+[A-Z][A-Za-z &]+,\s*\d+\s*\(.+$", "", candidate)
    candidate = candidate.strip(" .")
    return candidate if len(candidate) >= 10 else raw


def title_match_score(query_title: str, found_title: str, label: str = "") -> float:
    found_norm = normalize_title(found_title)
    candidates = [safe_text(query_title), citation_title_guess(query_title), safe_text(label), citation_title_guess(label)]
    scores: list[float] = []
    for candidate in candidates:
        candidate_norm = normalize_title(candidate)
        if not candidate_norm or not found_norm:
            continue
        if found_norm in candidate_norm or candidate_norm in found_norm:
            scores.append(0.96)
        scores.append(SequenceMatcher(None, candidate_norm, found_norm).ratio())
        left = title_words(candidate_norm)
        right = title_words(found_norm)
        if left and right:
            scores.append(len(left & right) / len(left | right))
            scores.append(len(left & right) / min(len(left), len(right)))
    return max(scores or [0.0])


def parse_jsonish(text: str) -> dict[str, object]:
    if not safe_text(text):
        return {}
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else {}
    except Exception:
        return {}


def parse_references(path: Path = REFERENCES) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8", errors="ignore")
    entries: dict[str, dict[str, str]] = {}
    starts = list(re.finditer(r"@\w+\s*\{\s*([^,\s]+)\s*,", text))
    for idx, match in enumerate(starts):
        key = match.group(1)
        start = match.end()
        end = starts[idx + 1].start() if idx + 1 < len(starts) else len(text)
        body = text[start:end]
        fields: dict[str, str] = {}
        for field_match in re.finditer(r"(?m)^\s*([A-Za-z0-9_-]+)\s*=\s*[\{\"](.+?)[\}\"],?\s*$", body):
            fields[field_match.group(1).lower()] = safe_text(field_match.group(2))
        entries[key] = fields
    return entries


def all_text(row: pd.Series, payload: dict[str, object]) -> str:
    pieces = [safe_text(value) for value in row.to_dict().values()]
    pieces.extend(safe_text(value) for value in payload.values())
    return " ".join(piece for piece in pieces if piece)


def extract_ids(text: str, payload: dict[str, object]) -> dict[str, list[str]]:
    doi_values = DOI_RE.findall(text)
    for key, value in payload.items():
        key_text = safe_text(key).lower()
        value_text = safe_text(value)
        if "doi" in key_text and value_text:
            doi_values.append(value_text)
        if key_text in {"paper_id", "id"} and value_text.lower().startswith("doi:"):
            doi_values.append(value_text)
    doi_values = [clean_doi(v) for v in doi_values]

    pmids: list[str] = []
    for match in PMID_RE.findall(text):
        pmids.extend([part for part in match if part])
    for key, value in payload.items():
        if "pmid" in safe_text(key).lower() or "pubmed" in safe_text(key).lower():
            pmids.extend(re.findall(r"\d{4,10}", safe_text(value)))

    pmcids = PMCID_RE.findall(text)
    pmcids.extend([f"PMC{digits}" for digits in PMCID_LABEL_RE.findall(text)])
    for key, value in payload.items():
        if "pmcid" in safe_text(key).lower() or "pmc" == safe_text(key).lower():
            pmcids.extend(PMCID_RE.findall(safe_text(value)))
            pmcids.extend([f"PMC{digits}" for digits in PMCID_LABEL_RE.findall(safe_text(value))])

    ncts = NCT_RE.findall(text)
    for key, value in payload.items():
        if "nct" in safe_text(key).lower() or safe_text(key).lower() in {"nct_id", "nctid"}:
            ncts.extend(NCT_RE.findall(safe_text(value)))

    urls = [url.rstrip(".,;)]}'\"") for url in URL_RE.findall(text)]
    aea_trials = unique(AEA_TRIAL_RE.findall(text))
    plos_dois = [f"10.1371/journal.pone.{digits}" for digits in PLOS_ARTICLE_RE.findall(text)]
    dataverse_ids = unique([value.upper() for value in DATAVERSE_DVN_RE.findall(text)])
    doi_values.extend(plos_dois)

    return {
        "doi": unique(doi_values),
        "pmid": unique(pmids),
        "pmcid": unique([v.upper() for v in pmcids]),
        "nct": unique([v.upper() for v in ncts]),
        "url": unique(urls),
        "aea_trial": aea_trials,
        "dataverse_dvn": dataverse_ids,
    }


def local_file_kind(path_text: str) -> str:
    path = safe_text(path_text)
    if not path:
        return "missing"
    if path.startswith("data/raw/corpus_candidates/"):
        return "external_corpus_mirror"
    if path.startswith("data/raw/replication_projects/"):
        return "mirrored_replication_project"
    if path.startswith("data/raw/"):
        return "raw_local_mirror"
    if path.startswith("data/derived/"):
        return "internal_derived_table"
    return "other_local_or_absolute_path"


def source_family_url(source_family: str) -> str:
    for needle, url in SOURCE_FAMILY_URLS.items():
        if needle.lower() in safe_text(source_family).lower():
            return url
    return ""


def crossref_cache_path(query: str) -> Path:
    return CROSSREF_CACHE / f"{stable_hash(query, length=24)}.json"


def fetch_crossref(query: str) -> dict[str, object]:
    CROSSREF_CACHE.mkdir(parents=True, exist_ok=True)
    cache_path = crossref_cache_path(query)
    if cache_path.exists():
        try:
            return json.loads(cache_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    params = urllib.parse.urlencode({"rows": "1", "query.bibliographic": query})
    url = f"https://api.crossref.org/works?{params}"
    payload: dict[str, object] = {"query": query, "url": url, "status": "not_attempted"}
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=20) as response:
            data = json.load(response)
        items = data.get("message", {}).get("items", [])
        payload = {"query": query, "url": url, "status": "ok", "first_item": items[0] if items else {}}
    except Exception as exc:
        payload = {"query": query, "url": url, "status": "error", "error": repr(exc)}
    cache_path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    time.sleep(0.1)
    return payload


def europepmc_cache_path(query: str) -> Path:
    return EUROPEPMC_CACHE / f"{stable_hash(query, length=24)}.json"


def fetch_europepmc(query: str) -> dict[str, object]:
    EUROPEPMC_CACHE.mkdir(parents=True, exist_ok=True)
    cache_path = europepmc_cache_path(query)
    if cache_path.exists():
        try:
            return json.loads(cache_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    params = urllib.parse.urlencode({"query": f'"{query}"', "format": "json", "pageSize": "5"})
    url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?{params}"
    payload: dict[str, object] = {"query": query, "url": url, "status": "not_attempted"}
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=20) as response:
            data = json.load(response)
        items = data.get("resultList", {}).get("result", [])
        payload = {"query": query, "url": url, "status": "ok", "items": items}
    except Exception as exc:
        payload = {"query": query, "url": url, "status": "error", "error": repr(exc)}
    cache_path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    time.sleep(0.1)
    return payload


def crossref_candidate_from_metabus(payload: dict[str, object], label: str) -> tuple[str, str, str, str]:
    haystack = " ".join([safe_text(payload.get("paper_id")), safe_text(payload.get("study_id")), safe_text(label)])
    match = METABUS_ID_RE.search(haystack)
    if not match:
        return "", "", "", ""
    code, volume, issue, page = match.groups()
    journal = JOURNAL_FOR_CODE.get(code.upper(), code.upper())
    year = safe_text(payload.get("year"))
    query = " ".join(part for part in [journal, year, volume, issue, page] if part)
    data = fetch_crossref(query)
    item = data.get("first_item") if isinstance(data, dict) else {}
    if not isinstance(item, dict) or not item:
        return "", "", "", safe_text(data.get("url") if isinstance(data, dict) else "")
    doi = clean_doi(safe_text(item.get("DOI")))
    title = "; ".join(item.get("title", [])) if isinstance(item.get("title"), list) else safe_text(item.get("title"))
    score = safe_text(item.get("score"))
    return doi, title, score, safe_text(data.get("url"))


def crossref_candidate_from_title(payload: dict[str, object], label: str) -> tuple[str, str, str, str, str]:
    title = safe_text(payload.get("title")) or safe_text(payload.get("original_title")) or safe_text(payload.get("replication_title"))
    if not title or re.fullmatch(r"[A-Za-z]+_\d+(?:_\d+)?", title):
        title = citation_title_guess(label)
    if not title or len(title) < 20:
        return "", "", "", "", ""
    year = safe_text(payload.get("year"))
    journal = safe_text(payload.get("journal"))
    query = " ".join(part for part in [title, journal, year] if part)
    data = fetch_crossref(query)
    item = data.get("first_item") if isinstance(data, dict) else {}
    if not isinstance(item, dict) or not item:
        return "", "", "", "", safe_text(data.get("url") if isinstance(data, dict) else "")
    doi = clean_doi(safe_text(item.get("DOI")))
    found_title = "; ".join(item.get("title", [])) if isinstance(item.get("title"), list) else safe_text(item.get("title"))
    ratio = title_match_score(title, found_title, label) if found_title else 0.0
    return doi, found_title, f"{ratio:.3f}", title, safe_text(data.get("url"))


def source_specific_candidate(payload: dict[str, object], row: pd.Series) -> tuple[str, str, str, str]:
    source_family = safe_text(row.get("source_family"))
    original_title = safe_text(payload.get("original_title"))
    label = safe_text(row.get("result_label"))
    study_id = safe_text(payload.get("study_id")) or safe_text(payload.get("paper_id")) or safe_text(payload.get("match_author"))

    lookup_keys = [original_title, label, study_id, safe_text(payload.get("outcome"))]
    if "button_nord" in source_family.lower() or "button_nord" in safe_text(payload.get("source_corpus")).lower():
        lookup_keys.append(safe_text(payload.get("outcome")))
    for key in lookup_keys:
        if key in SOURCE_SPECIFIC_RESOLUTIONS:
            item = SOURCE_SPECIFIC_RESOLUTIONS[key]
            return clean_doi(item["doi"]), item["title"], item["method"], item["note"]

    if "button_nord" in source_family.lower() or "button_nord" in safe_text(payload.get("source_corpus")).lower():
        first_author = (
            safe_text(payload.get("outcome"))
            or re.sub(r"_.*$", "", safe_text(payload.get("paper_id")))
            or re.sub(r"_.*$", "", safe_text(payload.get("study_id")))
        )
        ref = button_nord_reference_lookup(first_author)
        if ref:
            return ref

    rpcb_match = re.search(r"\bpaper_(\d+)_experiment_\d+\b", original_title)
    if rpcb_match:
        paper_number = rpcb_match.group(1)
        paper_file = ROOT / "data" / "raw" / "corpus_candidates" / "rpcb" / "RP_CB Final Analysis - Paper level data.csv"
        if paper_file.exists():
            try:
                papers = pd.read_csv(paper_file, dtype=str, keep_default_na=False)
                paper = papers.loc[papers["Paper #"].eq(paper_number)].head(1)
                if not paper.empty:
                    title = safe_text(paper.iloc[0].get("Original paper title"))
                    journal = safe_text(paper.iloc[0].get("Original paper journal"))
                    data = fetch_europepmc(title)
                    best_item: tuple[float, str, str] = (0.0, "", "")
                    for item in data.get("items", []) if isinstance(data, dict) else []:
                        item_title = safe_text(item.get("title"))
                        doi = clean_doi(safe_text(item.get("doi")))
                        score = title_match_score(title, item_title)
                        if normalize_title(item_title) == normalize_title(title):
                            score += 0.25
                        if journal and normalize_title(safe_text(item.get("journalTitle"))) == normalize_title(journal):
                            score += 0.10
                        if doi and score > best_item[0]:
                            best_item = (score, doi, item_title)
                    if best_item[1] and best_item[0] >= 0.90:
                        return best_item[1], best_item[2], "rpcb_paper_table_to_europepmc_exact_title", f"RPCB paper table maps {original_title} to Paper #{paper_number}: {title}"
                    return "", title, "rpcb_paper_table_title_no_doi", f"RPCB paper table maps {original_title} to Paper #{paper_number}; DOI lookup failed."
            except Exception:
                return "", "", "", ""

    return "", "", "", ""


def button_nord_reference_lookup(first_author: str) -> tuple[str, str, str, str]:
    author = safe_text(first_author)
    if not author:
        return "", "", "", ""
    html_path = ROOT / "data" / "raw" / "corpus_candidates" / "button_nord_neuroscience" / "power_up_pmc5566862.html"
    if not html_path.exists():
        return "", "", "", ""
    text = html_path.read_text(encoding="utf-8", errors="ignore")
    for match in re.finditer(r'<li id="B\d+">(.*?)</li>', text, flags=re.S | re.I):
        ref_id_match = re.search(r'id="(B\d+)"', match.group(0))
        ref_id = ref_id_match.group(1) if ref_id_match else ""
        block = match.group(1)
        plain = safe_text(re.sub(r"<[^>]+>", " ", block))
        if not re.match(rf"{re.escape(author)}\b", plain, flags=re.I):
            continue
        doi_match = DOI_RE.search(plain)
        doi = clean_doi(doi_match.group(0)) if doi_match else ""
        title_match = re.search(r"\((?:19|20)\d{2}[a-z]?\)\s+(.+?)\s+[A-Z][A-Za-z .&]+(?:\s+\d+[:;]|\s*$)", plain)
        title = safe_text(title_match.group(1)) if title_match else ""
        scholar_match = re.search(r'href="([^"]*scholar_lookup[^"]+)"', block)
        scholar_url = scholar_match.group(1).replace("&amp;", "&") if scholar_match else ""
        if doi or title:
            note = (
                f"https://pmc.ncbi.nlm.nih.gov/articles/PMC5566862/#{ref_id}; "
                f"Button/Nord workbook gives first-author label {author}; mirrored PMC article reference list maps it to this reference."
                + (f" Scholar lookup: {scholar_url}" if scholar_url else "")
            )
            return doi, title, "button_nord_local_pmc_reference_lookup", note
    return "", "", "", ""


def primary_url(ids: dict[str, list[str]], source_family: str, crossref_doi: str) -> tuple[str, str]:
    if ids["nct"]:
        return f"https://clinicaltrials.gov/study/{ids['nct'][0]}", "nct"
    if ids["aea_trial"]:
        return f"https://www.socialscienceregistry.org/trials/{ids['aea_trial'][0]}", "aea_trial"
    if ids["doi"]:
        return f"https://doi.org/{ids['doi'][0]}", "doi"
    if crossref_doi:
        return f"https://doi.org/{crossref_doi}", "crossref_doi"
    if ids["dataverse_dvn"]:
        return f"https://doi.org/10.7910/DVN/{ids['dataverse_dvn'][0]}", "dataverse_dvn"
    if ids["pmcid"]:
        return f"https://www.ncbi.nlm.nih.gov/pmc/articles/{ids['pmcid'][0]}/", "pmcid"
    if ids["pmid"]:
        return f"https://pubmed.ncbi.nlm.nih.gov/{ids['pmid'][0]}/", "pmid"
    if ids["url"]:
        return ids["url"][0], "url"
    family_url = source_family_url(source_family)
    if family_url:
        return family_url, "source_family_url"
    return "", ""


def grounding_status(ids: dict[str, list[str]], crossref_doi: str, crossref_status: str, primary_basis: str, local_kind: str) -> str:
    if ids["nct"]:
        return "registry_identifier_nct"
    if ids["aea_trial"]:
        return "registry_identifier_aea_trial"
    if ids["doi"] or ids["pmid"] or ids["pmcid"] or ids["dataverse_dvn"]:
        return "represented_work_identifier_in_source_row"
    if crossref_doi and crossref_status == "candidate_high_similarity":
        return "represented_work_crossref_resolved"
    if crossref_status == "source_specific_high_confidence":
        return "represented_work_source_specific_resolved"
    if crossref_doi:
        return "represented_work_crossref_candidate_low_similarity"
    if primary_basis == "url":
        return "represented_work_or_source_url_in_row"
    if primary_basis == "source_family_url":
        return "source_family_grounded_only"
    if local_kind == "internal_derived_table":
        return "internal_derived_only"
    return "unresolved"


def literal_number_status(source_directness: str, local_kind: str) -> str:
    if source_directness == "raw_ctgov_registry_row":
        return "literal_number_from_registry_mirror"
    if source_directness == "political_science_component_rows":
        return "literal_number_from_package_derived_rescue_row"
    if local_kind == "external_corpus_mirror":
        return "literal_number_from_external_corpus_mirror"
    if local_kind == "mirrored_replication_project":
        return "literal_number_from_replication_project_table"
    if local_kind == "internal_derived_table":
        return "literal_number_from_internal_derived_table"
    return "literal_number_from_local_file_unclear"


def evidence_level_for(row: dict[str, str]) -> tuple[int, str]:
    grounding = safe_text(row.get("grounding_status"))
    literal = safe_text(row.get("literal_number_status"))
    local_kind = safe_text(row.get("local_evidence_kind"))
    primary_url = safe_text(row.get("primary_real_world_url"))
    source_bib_url = safe_text(row.get("source_bib_real_world_url"))
    crossref_status = safe_text(row.get("crossref_resolution_status"))

    if literal == "literal_number_from_registry_mirror":
        return 6, "original_number_extracted"
    if literal in {"literal_number_from_author_output", "literal_number_from_author_table_or_log"}:
        return 6, "original_number_extracted"
    if literal == "literal_number_recomputed_from_raw":
        return 7, "recomputed_from_raw"
    if local_kind == "raw_local_mirror" and primary_url:
        return 5, "original_source_obtained"
    if local_kind == "internal_derived_table":
        if primary_url:
            return 4, "target_source_independently_grounded"
        if source_bib_url:
            return 1, "internal_trace_only"
        return 0, "unanchored_number"
    if primary_url and safe_text(row.get("primary_real_world_url_basis")) in {"aea_trial", "nct", "doi", "pmid", "pmcid", "dataverse_dvn"}:
        return 4, "target_source_independently_grounded"
    if primary_url and grounding in {
        "registry_identifier_aea_trial",
        "registry_identifier_nct",
        "represented_work_identifier_in_source_row",
        "represented_work_crossref_resolved",
        "represented_work_source_specific_resolved",
    } and crossref_status != "candidate_low_similarity":
        return 4, "target_source_independently_grounded"
    if grounding in {
        "registry_identifier_aea_trial",
        "registry_identifier_nct",
        "represented_work_identifier_in_source_row",
        "represented_work_crossref_resolved",
        "represented_work_source_specific_resolved",
    }:
        return 3, "external_assertion_with_target_source"
    if primary_url or source_bib_url or local_kind in {
        "external_corpus_mirror",
        "mirrored_replication_project",
        "raw_local_mirror",
    }:
        return 2, "external_source_assertion"
    return 0, "unanchored_number"


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def todo_for(row: dict[str, str]) -> list[dict[str, str]]:
    todos: list[dict[str, str]] = []
    srid = row["source_result_id"]
    if row["grounding_status"] in {"internal_derived_only", "unresolved"}:
        todos.append(
            {
                "source_result_id": srid,
                "todo_type": "find_real_world_identifier",
                "priority": "high",
                "detail": "No DOI/PMID/PMCID/NCT/source URL was recovered for the represented work; use title, corpus row ID, or source documentation to resolve it.",
                "starting_point": row["local_evidence_path"] or row["result_label"],
            }
        )
    if row["literal_number_status"] in {
        "literal_number_from_internal_derived_table",
        "literal_number_from_external_corpus_mirror",
        "literal_number_from_package_derived_rescue_row",
        "literal_number_from_replication_project_table",
    }:
        todos.append(
            {
                "source_result_id": srid,
                "todo_type": "verify_number_in_original_or_authoritative_source",
                "priority": "medium",
                "detail": "The plotted number is traceable locally, but the copied number is not yet verified against original paper/table/API text.",
                "starting_point": row["primary_real_world_url"] or row["local_evidence_path"],
            }
        )
    if row["crossref_resolution_status"] == "candidate_low_similarity":
        todos.append(
            {
                "source_result_id": srid,
                "todo_type": "review_crossref_candidate",
                "priority": "medium",
                "detail": "Crossref returned a candidate DOI with low title similarity; review before promoting.",
                "starting_point": row["crossref_query_url"],
            }
        )
    return todos


def markdown_table(headers: list[str], rows: list[list[object]]) -> str:
    def cell(value: object) -> str:
        return safe_text(value).replace("|", "\\|")

    return "\n".join(
        [
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join(["---"] * len(headers)) + " |",
            *["| " + " | ".join(cell(v) for v in row) + " |" for row in rows],
        ]
    )


def main() -> None:
    sr = read_tsv(SOURCE_RESULT)
    human = read_tsv(HUMAN_CHECK)
    references = parse_references()
    data = sr.merge(
        human[
            [
                "source_result_id",
                "source_family",
                "source_directness",
                "recovered_raw_file_repo_relative",
                "recovered_raw_file_sha256",
                "upstream_row_json",
                "plot_row_json",
            ]
        ],
        on="source_result_id",
        how="left",
    )

    rows: list[dict[str, str]] = []
    todos: list[dict[str, str]] = []
    for _, row in data.iterrows():
        payload = parse_jsonish(safe_text(row.get("verbatim_source_row_text"))) or parse_jsonish(safe_text(row.get("upstream_row_json")))
        text = all_text(row, payload)
        ids = extract_ids(text, payload)
        source_key = safe_text(row.get("source_citation_key"))
        source_bib = references.get(source_key, {})
        source_bib_doi = clean_doi(safe_text(source_bib.get("doi")))
        source_bib_url = safe_text(source_bib.get("url"))
        source_bib_title = safe_text(source_bib.get("title"))
        local_path = safe_text(row.get("recovered_raw_file_repo_relative"))
        local_kind = local_file_kind(local_path)

        crossref_doi = ""
        crossref_title = ""
        crossref_score = ""
        crossref_query_url = ""
        crossref_method = ""
        crossref_similarity = ""
        crossref_status = ""

        if not (ids["doi"] or ids["pmid"] or ids["pmcid"] or ids["nct"]):
            doi, title, score, query_url = crossref_candidate_from_metabus(payload, safe_text(row.get("result_label")))
            if doi:
                crossref_doi, crossref_title, crossref_score, crossref_query_url = doi, title, score, query_url
                crossref_method = "metabus_journal_volume_issue_page"
        if not (ids["doi"] or ids["pmid"] or ids["pmcid"] or ids["nct"] or crossref_doi):
            doi, title, method, note = source_specific_candidate(payload, row)
            if doi or title:
                crossref_doi, crossref_title, crossref_similarity = doi, title, "1.000" if doi else ""
                crossref_method = method
                crossref_query_url = note
                if doi or method == "button_nord_local_pmc_reference_lookup":
                    crossref_status = "source_specific_high_confidence"
        if not (ids["doi"] or ids["pmid"] or ids["pmcid"] or ids["nct"] or crossref_doi):
            doi, title, sim, query_title, query_url = crossref_candidate_from_title(payload, safe_text(row.get("result_label")))
            if doi:
                crossref_doi, crossref_title, crossref_similarity, crossref_query_url = doi, title, sim, query_url
                crossref_method = "title_year_journal"

        if not crossref_status and crossref_doi:
            sim = float(crossref_similarity or "1") if crossref_similarity else 1.0
            crossref_status = "candidate_high_similarity" if sim >= 0.80 else "candidate_low_similarity"
        elif not crossref_status and crossref_query_url:
            crossref_status = "queried_no_candidate"
        elif not crossref_status:
            crossref_status = "not_needed_or_not_attempted"

        url, basis = primary_url(ids, safe_text(row.get("source_family")), crossref_doi)
        if not url and crossref_status == "source_specific_high_confidence":
            url_match = URL_RE.search(crossref_query_url)
            if url_match:
                url, basis = url_match.group(0).rstrip(".,;)]}'\""), "source_specific_reference_url"
        status = grounding_status(ids, crossref_doi, crossref_status, basis, local_kind)
        literal_status = literal_number_status(safe_text(row.get("source_directness")), local_kind)
        row_out = {
            "source_result_id": safe_text(row.get("source_result_id")),
            "result_label": safe_text(row.get("result_label")),
            "source_family": safe_text(row.get("source_family")),
            "source_directness": safe_text(row.get("source_directness")),
            "coding_status": safe_text(row.get("coding_status")),
            "local_evidence_path": local_path,
            "local_evidence_sha256": safe_text(row.get("recovered_raw_file_sha256")),
            "local_evidence_kind": local_kind,
            "doi_list": " | ".join(ids["doi"]),
            "pmid_list": " | ".join(ids["pmid"]),
            "pmcid_list": " | ".join(ids["pmcid"]),
            "nct_list": " | ".join(ids["nct"]),
            "url_list": " | ".join(ids["url"]),
            "aea_trial_list": " | ".join(ids["aea_trial"]),
            "dataverse_dvn_list": " | ".join(ids["dataverse_dvn"]),
            "source_bib_key": source_key,
            "source_bib_doi": source_bib_doi,
            "source_bib_url": source_bib_url,
            "source_bib_title": source_bib_title,
            "source_bib_real_world_url": f"https://doi.org/{source_bib_doi}" if source_bib_doi else source_bib_url,
            "crossref_resolved_doi": crossref_doi,
            "crossref_resolved_title": crossref_title,
            "crossref_score": crossref_score,
            "crossref_title_similarity": crossref_similarity,
            "crossref_resolution_method": crossref_method,
            "crossref_resolution_status": crossref_status,
            "crossref_query_url": crossref_query_url,
            "primary_real_world_url": url,
            "primary_real_world_url_basis": basis,
            "grounding_status": status,
            "literal_number_status": literal_status,
            "number_verified_against_original_source": "yes" if literal_status == "literal_number_from_registry_mirror" else "not_yet",
            "grounding_note": (
                "NCT registry row is treated as authoritative registry source for the literal result."
                if basis == "nct"
                else "Real-world handle found, but the numeric result still needs original/source verification."
                if status not in {"internal_derived_only", "unresolved", "source_family_grounded_only"}
                else "Only corpus/source-family grounding or local derived evidence was recovered."
            ),
        }
        level, level_name = evidence_level_for(row_out)
        row_out["evidence_level"] = str(level)
        row_out["evidence_level_name"] = level_name
        row_out["source_is_original"] = bool_text(level_name in {"original_source_obtained", "original_number_extracted", "recomputed_from_raw"})
        row_out["number_verified_by_us"] = bool_text(level_name in {"original_number_extracted", "recomputed_from_raw"})
        row_out["represented_work_identified"] = bool_text(level >= 3)
        row_out["source_is_external"] = bool_text(row_out["local_evidence_kind"] != "internal_derived_table")
        row_out["requires_manual_review"] = bool_text(level < 5 or row_out["crossref_resolution_status"] == "candidate_low_similarity")
        row_out["conversion_verified"] = bool_text(level >= 6)
        rows.append(row_out)
        todos.extend(todo_for(row_out))

    rows_df = pd.DataFrame(rows)
    todos_df = pd.DataFrame(todos)
    if todos_df.empty:
        todos_df = pd.DataFrame(columns=["source_result_id", "todo_type", "priority", "detail", "starting_point"])

    summary_rows: list[dict[str, object]] = [
        {"metric": "sample_n", "value": len(rows_df)},
        {"metric": "rows_with_represented_identifier_or_candidate", "value": int((rows_df[["doi_list", "pmid_list", "pmcid_list", "nct_list", "aea_trial_list", "dataverse_dvn_list", "crossref_resolved_doi"]].apply(lambda col: col.map(safe_text).ne("")).any(axis=1)).sum())},
        {"metric": "rows_with_high_confidence_represented_identifier", "value": int(rows_df["grounding_status"].isin(["registry_identifier_aea_trial", "registry_identifier_nct", "represented_work_identifier_in_source_row", "represented_work_crossref_resolved"]).sum())},
        {"metric": "rows_with_source_bib_real_world_url", "value": int(rows_df["source_bib_real_world_url"].map(safe_text).ne("").sum())},
        {"metric": "rows_with_any_real_world_url", "value": int((rows_df["primary_real_world_url"].map(safe_text).ne("") | rows_df["source_bib_real_world_url"].map(safe_text).ne("")).sum())},
        {"metric": "rows_with_primary_real_world_url", "value": int(rows_df["primary_real_world_url"].map(safe_text).ne("").sum())},
        {"metric": "rows_verified_against_original_source", "value": int(rows_df["number_verified_against_original_source"].eq("yes").sum())},
        {"metric": "rows_still_need_original_number_verification", "value": int(rows_df["number_verified_against_original_source"].ne("yes").sum())},
    ]
    for column in ["local_evidence_kind", "grounding_status", "literal_number_status", "crossref_resolution_status"]:
        for key, value in rows_df[column].value_counts().sort_index().items():
            summary_rows.append({"metric": f"{column}::{key}", "value": int(value)})
    for key, value in rows_df["evidence_level_name"].value_counts().sort_index().items():
        summary_rows.append({"metric": f"evidence_level_name::{key}", "value": int(value)})
    for column in [
        "source_is_original",
        "number_verified_by_us",
        "represented_work_identified",
        "source_is_external",
        "requires_manual_review",
        "conversion_verified",
    ]:
        for key, value in rows_df[column].value_counts().sort_index().items():
            summary_rows.append({"metric": f"{column}::{key}", "value": int(value)})
    for key, value in todos_df["todo_type"].value_counts().sort_index().items():
        summary_rows.append({"metric": f"todo::{key}", "value": int(value)})

    summary_df = pd.DataFrame(summary_rows)
    below_level3 = rows_df.loc[rows_df["evidence_level"].astype(int) < 3].copy()
    if not below_level3.empty:
        below_level3["why_not_level3"] = below_level3.apply(
            lambda row: (
                "Mirrored workbook exposes only an anonymized study/article code and effect/N cells; no DOI, title, PMID, registry ID, or source-paper URL is present."
                if "schaefer_schwarz_2019" in safe_text(row.get("local_evidence_path")).lower()
                else "Mirrored SAV exposes only year and paper index for this sampled psychology article; no DOI, title, PMID, registry ID, or source-paper URL is present."
                if "linden_2024" in safe_text(row.get("local_evidence_path")).lower()
                else "No represented-paper handle was recovered."
            ),
            axis=1,
        )
        below_level3["next_manual_action"] = below_level3.apply(
            lambda row: (
                "Request the original article-key mapping from Schäfer/Schwarz or find an author-posted supplementary crosswalk; do not promote from the anonymized ID alone."
                if "schaefer_schwarz_2019" in safe_text(row.get("local_evidence_path")).lower()
                else "Request the coded article list for Linden et al. Study 2 / ATJ_Study2_ESs_and_Ns.sav; do not promote from year+paper-index alone."
                if "linden_2024" in safe_text(row.get("local_evidence_path")).lower()
                else "Manual bibliographic resolution required."
            ),
            axis=1,
        )
    else:
        below_level3 = pd.DataFrame(columns=list(rows_df.columns) + ["why_not_level3", "next_manual_action"])
    one_line_frame(rows_df).to_csv(OUT_ROWS, sep="\t", index=False)
    one_line_frame(todos_df).to_csv(OUT_TODOS, sep="\t", index=False)
    summary_df.to_csv(OUT_SUMMARY, sep="\t", index=False)
    one_line_frame(below_level3).to_csv(OUT_BELOW_LEVEL3, sep="\t", index=False)

    report = [
        f"# Real-World Grounding Report For {SAMPLE_N}-Row Pilot",
        "",
        "This pass attempts to trace each sampled plotted point from local provenance rows to durable real-world handles.",
        "",
        "## Summary",
        "",
        markdown_table(["Metric", "Value"], summary_df.astype(str).values.tolist()),
        "",
        "## Interpretation",
        "",
        "- `rows_with_any_durable_identifier` means DOI, PMID, PMCID, NCT, or Crossref-resolved DOI was recovered.",
        "- `rows_verified_against_original_source` is intentionally stricter: currently only direct ClinicalTrials.gov registry rows qualify automatically.",
        "- Rows with `literal_number_from_external_corpus_mirror` or `literal_number_from_internal_derived_table` are real-world-linkable but still need original-source numeric verification before final promotion.",
        "",
        "## Outputs",
        "",
        f"- `{OUT_ROWS.relative_to(ROOT)}`",
        f"- `{OUT_TODOS.relative_to(ROOT)}`",
        f"- `{OUT_SUMMARY.relative_to(ROOT)}`",
        f"- `{OUT_BELOW_LEVEL3.relative_to(ROOT)}`",
    ]
    OUT_REPORT.write_text("\n".join(report) + "\n", encoding="utf-8")

    print(f"Wrote {OUT_ROWS.relative_to(ROOT)}")
    print(f"Wrote {OUT_TODOS.relative_to(ROOT)}")
    print(f"Wrote {OUT_SUMMARY.relative_to(ROOT)}")
    print(f"Wrote {OUT_BELOW_LEVEL3.relative_to(ROOT)}")
    print(summary_df.to_string(index=False))


if __name__ == "__main__":
    main()
