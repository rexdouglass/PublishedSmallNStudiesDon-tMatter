#!/usr/bin/env python3
"""Probe local Cochrane package files against Schwab's CDSR.RData extract.

This is intentionally a pilot/debug script, not the final production pipeline.
It parses the local package files we have, exports matching CDSR rows for those
review IDs, and writes row-level diagnostics for exact raw-data matches.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import math
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter, defaultdict
from io import BytesIO, StringIO
from pathlib import Path
from typing import Any

import pandas as pd


CD_RE = re.compile(r"CD\d{6}", re.I)
NCT_RE = re.compile(r"\bNCT\d{8}\b", re.I)
ISRCTN_RE = re.compile(r"\bISRCTN\d+\b", re.I)
DOI_RE = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b", re.I)

DATA_SOURCE_MAP = {
    "PUB": "published_data_only",
    "MIX": "published_and_unpublished_data",
    "UNPUB": "unpublished_data_only",
    "SOUGHT": "published_data_only_unpublished_sought_not_used",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def cd_from_path(path: Path) -> str:
    match = CD_RE.search(path.name)
    return match.group(0).upper() if match else ""


def norm_text(value: Any) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    text = html.unescape(str(value))
    text = text.lower()
    text = re.sub(r"[_\W]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def norm_study_relaxed(value: Any) -> str:
    """Study-name key that ignores parenthetical labels like '(H)'.

    Cochrane RM5 study names sometimes append arm/source labels in parentheses
    that are absent from the Schwab CDSR.RData study.name field. We still rely
    on raw numeric equality after this relaxed candidate lookup.
    """
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    text = re.sub(r"\([^)]*\)", " ", str(value))
    return norm_text(text)


def local_name(tag: str) -> str:
    return tag.split("}", 1)[-1] if "}" in tag else tag


def as_float(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"nan", "na", "nr", "not estimable"}:
        return None
    if text in {"Infinity", "+Infinity", "Inf", "+Inf"}:
        return math.inf
    if text in {"-Infinity", "-Inf"}:
        return -math.inf
    try:
        return float(text)
    except ValueError:
        return None


def as_intish(value: Any) -> float | None:
    return as_float(value)


def almost_equal(a: Any, b: Any, tol: float = 1e-8) -> bool:
    af = as_float(a)
    bf = as_float(b)
    if af is None and bf is None:
        return True
    if af is None or bf is None:
        return False
    if math.isinf(af) or math.isinf(bf):
        return af == bf
    return abs(af - bf) <= tol


def compact_join(values: list[Any]) -> str:
    cleaned = []
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text and text not in cleaned:
            cleaned.append(text)
    return "; ".join(cleaned)


def source_class(raw: Any) -> str:
    text = str(raw or "").strip().upper()
    return DATA_SOURCE_MAP.get(text, "")


def read_csv_bytes(raw: bytes) -> pd.DataFrame:
    last_error: Exception | None = None
    for enc in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            text = raw.decode(enc)
            return pd.read_csv(StringIO(text), dtype=str, keep_default_na=False)
        except Exception as exc:  # pragma: no cover - diagnostic fallback
            last_error = exc
    raise RuntimeError(f"could not parse CSV bytes: {last_error}")


def find_first_text(root: ET.Element, tag_name: str) -> str:
    for elem in root.iter():
        if local_name(elem.tag) == tag_name and elem.text:
            return elem.text.strip()
    return ""


def parse_rm5(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    cd = cd_from_path(path)
    root = ET.parse(path).getroot()
    title = find_first_text(root, "TITLE")

    studies: list[dict[str, Any]] = []
    study_by_id: dict[str, dict[str, Any]] = {}
    for elem in root.iter():
        if local_name(elem.tag) != "STUDY":
            continue
        sid = elem.attrib.get("ID", "")
        name = elem.attrib.get("NAME", "")
        raw_source = elem.attrib.get("DATA_SOURCE", "")
        row = {
            "package_path": str(path),
            "package_type": "rm5",
            "review_id": cd,
            "review_title": title,
            "study_id": sid,
            "study_name": name,
            "study_name_norm": norm_text(name),
            "study_year": elem.attrib.get("YEAR", ""),
            "revman_data_source_raw": raw_source,
            "revman_data_source_class": source_class(raw_source),
            "study_collection": "included_or_analysis",
        }
        studies.append(row)
        study_by_id[sid] = row

    rows: list[dict[str, Any]] = []
    row_number = 0

    def walk(elem: ET.Element, context: dict[str, Any]) -> None:
        nonlocal row_number
        tag = local_name(elem.tag)
        next_context = dict(context)
        if tag == "COMPARISON":
            next_context["comparison_nr"] = elem.attrib.get("NO", "")
            next_context["comparison_id"] = elem.attrib.get("ID", "")
            next_context["comparison_name"] = find_direct_text(elem, "NAME")
        elif tag.endswith("_OUTCOME"):
            next_context["outcome_flag"] = tag.split("_", 1)[0]
            next_context["outcome_nr"] = elem.attrib.get("NO", "")
            next_context["outcome_id"] = elem.attrib.get("ID", "")
            next_context["outcome_name"] = find_direct_text(elem, "NAME")
            next_context["effect_measure"] = elem.attrib.get("EFFECT_MEASURE", "")

        if tag in {"DICH_DATA", "CONT_DATA", "IV_DATA", "IPD_DATA", "OEV_DATA", "GENERIC_DATA"}:
            row_number += 1
            sid = elem.attrib.get("STUDY_ID", "")
            study = study_by_id.get(sid, {})
            attrs = elem.attrib
            rows.append(
                {
                    "package_numeric_row_id": f"{cd}:rm5:{row_number}",
                    "package_path": str(path),
                    "package_type": "rm5",
                    "review_id": cd,
                    "review_title": title,
                    "comparison_nr": next_context.get("comparison_nr", ""),
                    "comparison_id": next_context.get("comparison_id", ""),
                    "comparison_name": next_context.get("comparison_name", ""),
                    "outcome_nr": next_context.get("outcome_nr", ""),
                    "outcome_id": next_context.get("outcome_id", ""),
                    "outcome_name": next_context.get("outcome_name", ""),
                    "outcome_flag": next_context.get("outcome_flag", ""),
                    "data_tag": tag,
                    "effect_measure": next_context.get("effect_measure", ""),
                    "study_id": sid,
                    "study_name": study.get("study_name", ""),
                    "study_name_norm": study.get("study_name_norm", ""),
                    "study_year": study.get("study_year", ""),
                    "revman_data_source_raw": study.get("revman_data_source_raw", ""),
                    "revman_data_source_class": study.get("revman_data_source_class", ""),
                    "mean1": attrs.get("MEAN_1", ""),
                    "mean2": attrs.get("MEAN_2", ""),
                    "sd1": attrs.get("SD_1", ""),
                    "sd2": attrs.get("SD_2", ""),
                    "total1": attrs.get("TOTAL_1", ""),
                    "total2": attrs.get("TOTAL_2", ""),
                    "events1": attrs.get("EVENTS_1", ""),
                    "events2": attrs.get("EVENTS_2", ""),
                    "effect_size_package": attrs.get("EFFECT_SIZE", ""),
                    "log_effect_size_package": attrs.get("LOG_EFFECT_SIZE", ""),
                    "estimate_package": attrs.get("ESTIMATE", ""),
                    "se_package": attrs.get("SE", ""),
                    "oe_package": attrs.get("O_E", ""),
                    "var_package": attrs.get("VAR", ""),
                    "order_package": attrs.get("ORDER", ""),
                }
            )

        for child in elem:
            walk(child, next_context)

    walk(root, {})

    manifest = {
        "package_path": str(path),
        "package_file": path.name,
        "package_type": "rm5",
        "package_sha256": sha256_file(path),
        "package_size_bytes": path.stat().st_size,
        "review_id": cd,
        "review_title": title,
        "n_studies_parsed": len(studies),
        "n_numeric_rows_parsed": len(rows),
        "n_reference_rows_parsed": 0,
        "parse_status": "ok",
        "parse_warning": "",
    }
    return manifest, studies, rows


def find_direct_text(elem: ET.Element, tag_name: str) -> str:
    for child in elem:
        if local_name(child.tag) == tag_name and child.text:
            return child.text.strip()
    return ""


def ris_records(text: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    current: dict[str, list[str]] = defaultdict(list)
    raw_lines: list[str] = []
    last_tag = ""
    for line in text.splitlines():
        raw_lines.append(line)
        match = re.match(r"^([A-Z0-9]{2})\s*-\s?(.*)$", line)
        if match:
            tag, value = match.group(1), match.group(2).strip()
            if tag == "ER":
                rec = {key: vals[:] for key, vals in current.items()}
                rec["RAW"] = ["\n".join(raw_lines)]
                records.append(rec)
                current = defaultdict(list)
                raw_lines = []
                last_tag = ""
            else:
                current[tag].append(value)
                last_tag = tag
        elif last_tag and line.strip():
            current[last_tag][-1] += " " + line.strip()
    if current:
        rec = {key: vals[:] for key, vals in current.items()}
        rec["RAW"] = ["\n".join(raw_lines)]
        records.append(rec)
    return records


def classify_reference(rec: dict[str, Any]) -> str:
    ty = compact_join(rec.get("TY", [])).upper()
    raw = " ".join(compact_join(rec.get(tag, [])) for tag in rec)
    low = raw.lower()
    if re.search(r"\bclinicaltrials\.gov\b|\bNCT\d{8}\b|who ictrp|\bictrp\b|\bisrctn\d+\b|eudract|euctr|actrn|anzctr|drks|chictr|jprn|umin|ctri|irct|rebec", raw, re.I):
        return "registry_record"
    if re.search(r"\bfda\b|drugs@fda|medical review|statistical review|clinical review|ema\b|european medicines agency|epar|clinical study report|\bcsr\b|regulatory submission", raw, re.I):
        return "regulatory_or_csr"
    if ty == "PCOMM" or "personal communication" in low or "data supplied by author" in low or "unpublished information supplied" in low:
        return "author_correspondence"
    if ty == "UNPB" or "unpublished" in low or "data on file" in low or "sponsor data" in low or "company report" in low or "manufacturer report" in low:
        return "unpublished_data"
    if ty == "CPAPER" or re.search(r"conference|congress|meeting|symposium|proceedings|abstract|poster|oral presentation", low):
        return "conference_abstract"
    if re.search(r"dissertation|thesis|technical report|government report", low):
        return "thesis_or_report"
    if ty in {"BOOK", "CHAP"}:
        return "book_or_chapter"
    if ty == "JOUR":
        return "journal_article"
    return "other_or_unclear"


def parse_zip(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    cd = cd_from_path(path)
    studies: list[dict[str, Any]] = []
    numeric_rows: list[dict[str, Any]] = []
    refs: list[dict[str, Any]] = []
    warnings: list[str] = []
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        study_info_names = [n for n in names if n.lower().endswith(".csv") and "study-information" in n.lower()]
        data_row_names = [n for n in names if n.lower().endswith(".csv") and "data-rows" in n.lower()]
        ris_names = [n for n in names if n.lower().endswith(".ris")]

        for name in study_info_names:
            try:
                df = read_csv_bytes(zf.read(name))
            except Exception as exc:
                warnings.append(f"study-info parse failed {name}: {exc}")
                continue
            collection = "included"
            low_name = name.lower()
            if "awaiting" in low_name:
                collection = "awaiting"
            elif "ongoing" in low_name:
                collection = "ongoing"
            elif "excluded" in low_name:
                collection = "excluded"
            for idx, rec in df.iterrows():
                raw_source = rec.get("Data source", "")
                study = rec.get("Study", "")
                studies.append(
                    {
                        "package_path": str(path),
                        "package_type": "zip",
                        "review_id": cd,
                        "review_title": "",
                        "study_id": "",
                        "study_name": study,
                        "study_name_norm": norm_text(study),
                        "study_year": rec.get("Year", ""),
                        "revman_data_source_raw": raw_source,
                        "revman_data_source_class": source_class(raw_source),
                        "study_collection": collection,
                        "study_info_file": name,
                        "study_doi_ids": compact_join(DOI_RE.findall(" ".join(str(x) for x in rec.values))),
                        "study_nct_ids": compact_join([x.upper() for x in NCT_RE.findall(" ".join(str(x) for x in rec.values))]),
                        "study_isrctn_ids": compact_join([x.upper() for x in ISRCTN_RE.findall(" ".join(str(x) for x in rec.values))]),
                    }
                )

        study_by_norm: dict[str, dict[str, Any]] = {}
        for study in studies:
            if study.get("study_collection") == "included" and study.get("study_name_norm"):
                study_by_norm.setdefault(study["study_name_norm"], study)

        row_number = 0
        for name in data_row_names:
            try:
                df = read_csv_bytes(zf.read(name))
            except Exception as exc:
                warnings.append(f"analysis-row parse failed {name}: {exc}")
                continue
            for idx, rec in df.iterrows():
                row_number += 1
                study_name = rec.get("Study", "")
                study = study_by_norm.get(norm_text(study_name), {})
                numeric_rows.append(
                    {
                        "package_numeric_row_id": f"{cd}:zip:{row_number}",
                        "package_path": str(path),
                        "package_type": "zip",
                        "review_id": cd,
                        "review_title": "",
                        "comparison_nr": rec.get("Analysis group", ""),
                        "comparison_id": "",
                        "comparison_name": "",
                        "outcome_nr": rec.get("Analysis number", ""),
                        "outcome_id": "",
                        "outcome_name": rec.get("Analysis name", ""),
                        "outcome_flag": "",
                        "data_tag": "DATA_ROW_CSV",
                        "effect_measure": "",
                        "study_id": "",
                        "study_name": study_name,
                        "study_name_norm": norm_text(study_name),
                        "study_year": rec.get("Study year", ""),
                        "revman_data_source_raw": study.get("revman_data_source_raw", ""),
                        "revman_data_source_class": study.get("revman_data_source_class", ""),
                        "mean1": rec.get("Experimental mean", ""),
                        "mean2": rec.get("Control mean", ""),
                        "sd1": rec.get("Experimental SD", ""),
                        "sd2": rec.get("Control SD", ""),
                        "total1": rec.get("Experimental N", ""),
                        "total2": rec.get("Control N", ""),
                        "events1": rec.get("Experimental cases", ""),
                        "events2": rec.get("Control cases", ""),
                        "effect_size_package": rec.get("Mean", ""),
                        "log_effect_size_package": "",
                        "estimate_package": rec.get("GIV Mean", ""),
                        "se_package": rec.get("GIV SE", ""),
                        "oe_package": rec.get("O-E", ""),
                        "var_package": rec.get("Variance", ""),
                        "order_package": "",
                        "analysis_row_file": name,
                        "analysis_footnotes": rec.get("Footnotes", ""),
                    }
                )

        ref_number = 0
        for name in ris_names:
            try:
                text = zf.read(name).decode("utf-8-sig", errors="replace")
            except Exception as exc:
                warnings.append(f"RIS decode failed {name}: {exc}")
                continue
            collection = "included" if "included" in name.lower() else "diagnostic"
            if "awaiting" in name.lower():
                collection = "awaiting"
            elif "ongoing" in name.lower():
                collection = "ongoing"
            elif "excluded" in name.lower():
                collection = "excluded"
            for rec in ris_records(text):
                ref_number += 1
                raw = compact_join(rec.get("RAW", []))
                title = compact_join(rec.get("TI", []) + rec.get("T1", []) + rec.get("CT", []))
                ns = compact_join(rec.get("NS", []))
                refs.append(
                    {
                        "package_reference_id": f"{cd}:ris:{ref_number}",
                        "package_path": str(path),
                        "package_type": "zip",
                        "review_id": cd,
                        "ris_file": name,
                        "reference_collection": collection,
                        "study_name": ns,
                        "study_name_norm": norm_text(ns),
                        "ris_type": compact_join(rec.get("TY", [])),
                        "reference_title": title,
                        "reference_source_type": classify_reference(rec),
                        "pmids": compact_join(re.findall(r"\bPMID:?\s*(\d+)\b", raw, re.I) + rec.get("C3", [])),
                        "dois": compact_join(DOI_RE.findall(raw)),
                        "nct_ids": compact_join([x.upper() for x in NCT_RE.findall(raw)]),
                        "isrctn_ids": compact_join([x.upper() for x in ISRCTN_RE.findall(raw)]),
                    }
                )

    manifest = {
        "package_path": str(path),
        "package_file": path.name,
        "package_type": "zip",
        "package_sha256": sha256_file(path),
        "package_size_bytes": path.stat().st_size,
        "review_id": cd,
        "review_title": "",
        "n_studies_parsed": len(studies),
        "n_numeric_rows_parsed": len(numeric_rows),
        "n_reference_rows_parsed": len(refs),
        "parse_status": "ok",
        "parse_warning": " | ".join(warnings),
    }
    return manifest, studies, numeric_rows, refs


def export_cdsr_subset(cdsr_rdata: Path, cd_ids: list[str], out_csv: Path) -> None:
    quoted = ", ".join(f'"{cd}"' for cd in cd_ids)
    r_code = f"""
load({str(cdsr_rdata)!r})
d <- as.data.frame(data)
d$cochrane_effects_row <- as.integer(rownames(d))
d$id <- as.character(d$id)
d <- d[d$id %in% c({quoted}), ]
write.csv(d, {str(out_csv)!r}, row.names=FALSE, na="")
"""
    subprocess.run(["Rscript", "--vanilla", "-e", r_code], check=True)


def match_kind(pkg: pd.Series, cdsr: pd.Series) -> tuple[bool, str]:
    flag = str(pkg.get("outcome_flag", ""))
    if flag == "CONT":
        checks = [
            ("mean1", "mean1"),
            ("mean2", "mean2"),
            ("sd1", "sd1"),
            ("sd2", "sd2"),
            ("total1", "total1"),
            ("total2", "total2"),
        ]
        ok = all(almost_equal(pkg.get(a), cdsr.get(b)) for a, b in checks)
        return ok, "exact_continuous_raw_values" if ok else "continuous_raw_mismatch"
    if flag == "DICH":
        checks = [
            ("events1", "events1"),
            ("events2", "events2"),
            ("total1", "total1"),
            ("total2", "total2"),
        ]
        ok = all(almost_equal(pkg.get(a), cdsr.get(b)) for a, b in checks)
        return ok, "exact_dichotomous_raw_values" if ok else "dichotomous_raw_mismatch"
    if flag == "IV":
        ok_est = almost_equal(pkg.get("estimate_package"), cdsr.get("effect.es"), tol=1e-6) or almost_equal(
            pkg.get("log_effect_size_package"), cdsr.get("effect.es"), tol=1e-6
        )
        ok_se = almost_equal(pkg.get("se_package"), cdsr.get("effect.se"), tol=1e-6)
        ok = ok_est and ok_se
        return ok, "exact_inverse_variance_estimate_se" if ok else "inverse_variance_mismatch"
    return False, f"unsupported_flag_{flag or 'blank'}"


def aggregate_reference_evidence(refs: pd.DataFrame) -> pd.DataFrame:
    if refs.empty:
        return pd.DataFrame()
    included = refs[refs["reference_collection"].isin(["included", "awaiting", "ongoing"])].copy()
    if included.empty:
        return pd.DataFrame()
    rows = []
    for (review_id, study_norm), group in included.groupby(["review_id", "study_name_norm"], dropna=False):
        counts = Counter(group["reference_source_type"].fillna(""))
        rows.append(
            {
                "review_id": review_id,
                "study_name_norm": study_norm,
                "n_reference_rows": len(group),
                "n_journal_refs": counts.get("journal_article", 0),
                "n_conference_refs": counts.get("conference_abstract", 0),
                "n_registry_refs": counts.get("registry_record", 0),
                "n_regulatory_or_csr_refs": counts.get("regulatory_or_csr", 0),
                "n_unpublished_refs": counts.get("unpublished_data", 0),
                "n_author_correspondence_refs": counts.get("author_correspondence", 0),
                "n_thesis_or_report_refs": counts.get("thesis_or_report", 0),
                "n_other_refs": counts.get("other_or_unclear", 0) + counts.get("book_or_chapter", 0),
                "all_ref_types": compact_join(sorted(counts)),
                "dois": compact_join(group["dois"].tolist()),
                "pmids": compact_join(group["pmids"].tolist()),
                "nct_ids": compact_join(group["nct_ids"].tolist()),
                "isrctn_ids": compact_join(group["isrctn_ids"].tolist()),
                "reference_titles": compact_join(group["reference_title"].head(5).tolist()),
            }
        )
    return pd.DataFrame(rows)


def provenance_from_row(row: pd.Series) -> tuple[str, str, str, float]:
    src = str(row.get("revman_data_source_class", "") or "")
    n_journal = int(row.get("n_journal_refs", 0) or 0)
    n_nonjournal = sum(int(row.get(col, 0) or 0) for col in [
        "n_conference_refs",
        "n_registry_refs",
        "n_regulatory_or_csr_refs",
        "n_unpublished_refs",
        "n_author_correspondence_refs",
        "n_thesis_or_report_refs",
    ])
    if src == "unpublished_data_only":
        return "unpublished_or_author_supplied_likely", "nonjournal_likely", "RevMan DATA_SOURCE=UNPUB", 0.65
    if src == "published_and_unpublished_data":
        return "journal_plus_nonjournal_mixed", "mixed", "RevMan DATA_SOURCE=MIX", 0.65
    if src in {"published_data_only", "published_data_only_unpublished_sought_not_used"}:
        if n_journal and not n_nonjournal:
            return "journal_only_likely", "journal_likely", f"RevMan DATA_SOURCE={row.get('revman_data_source_raw')} plus only journal refs", 0.70
        if n_journal and n_nonjournal:
            return "journal_plus_nonjournal_mixed", "mixed", f"RevMan DATA_SOURCE={row.get('revman_data_source_raw')} but reference set is mixed", 0.65
        return "published_source_likely_no_refs", "journal_likely", f"RevMan DATA_SOURCE={row.get('revman_data_source_raw')}; no references in package", 0.55
    if n_journal and not n_nonjournal:
        return "journal_only_likely", "journal_likely", "reference-set heuristic: only journal references", 0.50
    if n_nonjournal and not n_journal:
        if int(row.get("n_registry_refs", 0) or 0):
            return "registry_only_likely", "nonjournal_likely", "reference-set heuristic: registry/nonjournal only", 0.50
        if int(row.get("n_regulatory_or_csr_refs", 0) or 0):
            return "regulatory_or_csr_likely", "nonjournal_likely", "reference-set heuristic: regulatory/CSR only", 0.50
        return "nonjournal_likely_unspecified", "nonjournal_likely", "reference-set heuristic: nonjournal only", 0.50
    if n_journal and n_nonjournal:
        return "journal_plus_nonjournal_mixed", "mixed", "reference-set heuristic: journal plus nonjournal references", 0.50
    return "unknown", "unknown", "no study source flag or reference evidence", 0.10


def published_vs_unpublished(row: pd.Series) -> str:
    src = str(row.get("revman_data_source_class", "") or "")
    if src in {"published_data_only", "published_data_only_unpublished_sought_not_used"}:
        return "published_only"
    if src == "published_and_unpublished_data":
        return "mixed_published_unpublished"
    if src == "unpublished_data_only":
        return "unpublished_only"
    return "unknown"


def build_matches(pkg_rows: pd.DataFrame, cdsr: pd.DataFrame, ref_agg: pd.DataFrame) -> pd.DataFrame:
    if pkg_rows.empty or cdsr.empty:
        return pd.DataFrame()

    for frame in (pkg_rows, cdsr):
        frame["review_id"] = frame["review_id" if "review_id" in frame.columns else "id"].astype(str)

    cdsr = cdsr.copy()
    cdsr["study_name_norm"] = cdsr["study.name"].map(norm_text)
    cdsr["study_name_norm_relaxed"] = cdsr["study.name"].map(norm_study_relaxed)
    cdsr["comparison_nr_str"] = cdsr["comparison.nr"].astype(str)
    cdsr["outcome_nr_str"] = cdsr["outcome.nr"].astype(str)
    cdsr["outcome_flag_str"] = cdsr["outcome.flag"].astype(str)

    pkg_rows = pkg_rows.copy()
    pkg_rows["study_name_norm_relaxed"] = pkg_rows["study_name"].map(norm_study_relaxed)
    pkg_rows["comparison_nr_str"] = pkg_rows["comparison_nr"].astype(str)
    pkg_rows["outcome_nr_str"] = pkg_rows["outcome_nr"].astype(str)
    pkg_rows["outcome_flag_str"] = pkg_rows["outcome_flag"].astype(str)

    candidate_index: dict[tuple[str, str, str, str, str], list[int]] = defaultdict(list)
    for idx, rec in cdsr.iterrows():
        for study_key in {str(rec.get("study_name_norm", "")), str(rec.get("study_name_norm_relaxed", ""))}:
            key = (
                str(rec.get("id", "")),
                study_key,
                str(rec.get("comparison_nr_str", "")),
                str(rec.get("outcome_nr_str", "")),
                str(rec.get("outcome_flag_str", "")),
            )
            candidate_index[key].append(idx)

    matches: list[dict[str, Any]] = []
    for _, pkg in pkg_rows.iterrows():
        key = (
            str(pkg.get("review_id", "")),
            str(pkg.get("study_name_norm", "")),
            str(pkg.get("comparison_nr_str", "")),
            str(pkg.get("outcome_nr_str", "")),
            str(pkg.get("outcome_flag_str", "")),
        )
        candidate_ids = candidate_index.get(key, [])
        study_match_key_type = "exact_normalized_study_name"
        if not candidate_ids:
            relaxed_key = (
                str(pkg.get("review_id", "")),
                str(pkg.get("study_name_norm_relaxed", "")),
                str(pkg.get("comparison_nr_str", "")),
                str(pkg.get("outcome_nr_str", "")),
                str(pkg.get("outcome_flag_str", "")),
            )
            candidate_ids = candidate_index.get(relaxed_key, [])
            study_match_key_type = "relaxed_parenthetical_study_name" if candidate_ids else "none"
        candidates = cdsr.loc[sorted(set(candidate_ids))]
        exact = []
        reasons = []
        for _, cand in candidates.iterrows():
            ok, reason = match_kind(pkg, cand)
            reasons.append(reason)
            if ok:
                exact.append(cand)
        if not exact:
            matches.append(
                {
                    "package_numeric_row_id": pkg.get("package_numeric_row_id", ""),
                    "review_id": pkg.get("review_id", ""),
                    "study_name": pkg.get("study_name", ""),
                    "comparison_nr": pkg.get("comparison_nr", ""),
                    "outcome_nr": pkg.get("outcome_nr", ""),
                    "outcome_flag": pkg.get("outcome_flag", ""),
                    "match_status": "no_exact_match",
                    "candidate_count": len(candidates),
                    "study_match_key_type": study_match_key_type,
                    "match_reason": compact_join(reasons[:5]),
                    "cochrane_effects_row": "",
                    "study_id_sha1": "",
                    "z": "",
                    "effect_N": "",
                    "effect_es": "",
                    "effect_se": "",
                    "outcome_group": "",
                    "RCT": "",
                    "revman_data_source_raw": pkg.get("revman_data_source_raw", ""),
                    "revman_data_source_class": pkg.get("revman_data_source_class", ""),
                }
            )
            continue
        for cand in exact:
            ok, reason = match_kind(pkg, cand)
            matches.append(
                {
                    "package_numeric_row_id": pkg.get("package_numeric_row_id", ""),
                    "review_id": pkg.get("review_id", ""),
                    "study_name": pkg.get("study_name", ""),
                    "comparison_nr": pkg.get("comparison_nr", ""),
                    "outcome_nr": pkg.get("outcome_nr", ""),
                    "outcome_flag": pkg.get("outcome_flag", ""),
                    "match_status": "exact_raw_match",
                    "candidate_count": len(candidates),
                    "study_match_key_type": study_match_key_type,
                    "match_reason": reason,
                    "cochrane_effects_row": cand.get("cochrane_effects_row", ""),
                    "study_id_sha1": cand.get("study.id.sha1", ""),
                    "z": cand.get("z", ""),
                    "effect_N": cand.get("effect.N", ""),
                    "effect_es": cand.get("effect.es", ""),
                    "effect_se": cand.get("effect.se", ""),
                    "outcome_group": cand.get("outcome.group", ""),
                    "RCT": cand.get("RCT", ""),
                    "revman_data_source_raw": pkg.get("revman_data_source_raw", ""),
                    "revman_data_source_class": pkg.get("revman_data_source_class", ""),
                }
            )

    out = pd.DataFrame(matches)
    if out.empty:
        return out

    if not ref_agg.empty:
        out["study_name_norm"] = out["study_name"].map(norm_text)
        out = out.merge(ref_agg, how="left", on=["review_id", "study_name_norm"])
    for col in [
        "n_reference_rows",
        "n_journal_refs",
        "n_conference_refs",
        "n_registry_refs",
        "n_regulatory_or_csr_refs",
        "n_unpublished_refs",
        "n_author_correspondence_refs",
        "n_thesis_or_report_refs",
        "n_other_refs",
    ]:
        if col not in out.columns:
            out[col] = 0
        out[col] = out[col].fillna(0).astype(int)
    for col in ["all_ref_types", "dois", "pmids", "nct_ids", "isrctn_ids", "reference_titles"]:
        if col not in out.columns:
            out[col] = ""
        out[col] = out[col].fillna("")

    provenance = out.apply(provenance_from_row, axis=1, result_type="expand")
    provenance.columns = [
        "provenance_class",
        "journal_vs_nonjournal",
        "provenance_decision_rule",
        "numeric_source_confidence",
    ]
    out = pd.concat([out, provenance], axis=1)
    out["published_vs_unpublished"] = out.apply(published_vs_unpublished, axis=1)
    out["numeric_source_inference_level"] = out["revman_data_source_class"].map(
        lambda x: "study_level_revman_flag" if str(x or "") else "unmatched_unknown"
    )
    return out


def write_summary(
    out_path: Path,
    manifests: pd.DataFrame,
    studies: pd.DataFrame,
    refs: pd.DataFrame,
    numeric_rows: pd.DataFrame,
    cdsr: pd.DataFrame,
    matches: pd.DataFrame,
) -> None:
    lines = ["# Cochrane Package Pilot Summary", ""]
    lines.append(f"Package files parsed: {len(manifests)}")
    if not manifests.empty:
        lines.append("")
        lines.append("## Packages")
        lines.append("")
        for _, row in manifests.sort_values(["package_type", "review_id"]).iterrows():
            lines.append(
                f"- {row['review_id']} `{row['package_file']}` ({row['package_type']}): "
                f"{row['n_studies_parsed']} studies, {row['n_numeric_rows_parsed']} numeric rows, "
                f"{row['n_reference_rows_parsed']} reference rows"
            )
    lines.append("")
    lines.append("## OSF/CDSR Overlap")
    lines.append("")
    if cdsr.empty:
        lines.append("No CDSR rows were exported for these review IDs.")
    else:
        counts = cdsr.groupby("id").size().sort_index()
        for review_id, n in counts.items():
            lines.append(f"- {review_id}: {n} CDSR.RData rows")
    lines.append("")
    lines.append("## Study Data Source Flags")
    lines.append("")
    if studies.empty:
        lines.append("No study rows parsed.")
    else:
        src_counts = studies.groupby(["review_id", "revman_data_source_raw"], dropna=False).size().reset_index(name="n")
        for _, row in src_counts.sort_values(["review_id", "revman_data_source_raw"]).iterrows():
            lines.append(f"- {row['review_id']} {row['revman_data_source_raw'] or '(blank)'}: {row['n']}")
    lines.append("")
    lines.append("## Exact Numeric Matches")
    lines.append("")
    if matches.empty:
        lines.append("No match diagnostics produced.")
    else:
        exact = matches[matches["match_status"] == "exact_raw_match"].copy()
        lines.append(f"Exact package-to-CDSR raw-data matches: {len(exact)}")
        lines.append(f"Unmatched package numeric rows: {(matches['match_status'] != 'exact_raw_match').sum()}")
        if not exact.empty:
            class_counts = exact["journal_vs_nonjournal"].value_counts(dropna=False)
            lines.append("")
            lines.append("journal_vs_nonjournal among exact matches:")
            for key, value in class_counts.items():
                lines.append(f"- {key}: {value}")
            pub_counts = exact["published_vs_unpublished"].value_counts(dropna=False)
            lines.append("")
            lines.append("published_vs_unpublished among exact matches:")
            for key, value in pub_counts.items():
                lines.append(f"- {key}: {value}")
            prov_counts = exact["provenance_class"].value_counts(dropna=False)
            lines.append("")
            lines.append("provenance_class among exact matches:")
            for key, value in prov_counts.items():
                lines.append(f"- {key}: {value}")
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "For legacy `StatsDataOnly.rm5` files, exact numeric matching is possible, but most files expose only "
        "RevMan study-level `DATA_SOURCE` flags, not the full citation list. That supports a coarse published-only "
        "versus mixed/unpublished flag, not exact journal-vs-registry numeric provenance."
    )
    lines.append(
        "Modern data-package ZIPs expose RIS references and study-information source flags, but current review "
        "packages may not overlap the historical CDSR snapshot used by Schwab."
    )
    out_path.write_text("\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packages", default="data/raw/cochrane_packages")
    parser.add_argument("--cdsr-rdata", default="data/raw/osf/CDSR.RData")
    parser.add_argument("--effects", default="data/raw/osf/CochraneEffects.csv")
    parser.add_argument("--out", default="data/derived")
    parser.add_argument("--interim", default="data/interim")
    args = parser.parse_args()

    packages_dir = Path(args.packages)
    out_dir = Path(args.out)
    interim_dir = Path(args.interim)
    out_dir.mkdir(parents=True, exist_ok=True)
    interim_dir.mkdir(parents=True, exist_ok=True)

    files = sorted([p for p in packages_dir.iterdir() if p.suffix.lower() in {".rm5", ".zip"}])
    manifests: list[dict[str, Any]] = []
    studies: list[dict[str, Any]] = []
    numeric_rows: list[dict[str, Any]] = []
    refs: list[dict[str, Any]] = []

    for path in files:
        try:
            if path.suffix.lower() == ".rm5":
                manifest, s, n = parse_rm5(path)
                r: list[dict[str, Any]] = []
            else:
                manifest, s, n, r = parse_zip(path)
        except Exception as exc:
            manifest = {
                "package_path": str(path),
                "package_file": path.name,
                "package_type": path.suffix.lower().lstrip("."),
                "package_sha256": sha256_file(path),
                "package_size_bytes": path.stat().st_size,
                "review_id": cd_from_path(path),
                "review_title": "",
                "n_studies_parsed": 0,
                "n_numeric_rows_parsed": 0,
                "n_reference_rows_parsed": 0,
                "parse_status": "error",
                "parse_warning": repr(exc),
            }
            s, n, r = [], [], []
        manifests.append(manifest)
        studies.extend(s)
        numeric_rows.extend(n)
        refs.extend(r)

    manifests_df = pd.DataFrame(manifests)
    studies_df = pd.DataFrame(studies)
    numeric_df = pd.DataFrame(numeric_rows)
    refs_df = pd.DataFrame(refs)

    manifests_df.to_csv(out_dir / "package_manifest.csv", index=False)
    studies_df.to_csv(out_dir / "package_study_sources.csv", index=False)
    numeric_df.to_csv(out_dir / "package_numeric_rows.csv", index=False)
    refs_df.to_csv(out_dir / "package_reference_sources.csv", index=False)

    cd_ids = sorted({cd for cd in manifests_df.get("review_id", pd.Series(dtype=str)).dropna().astype(str) if cd})
    cdsr_csv = interim_dir / "cdsr_package_review_subset.csv"
    if Path(args.cdsr_rdata).exists() and cd_ids:
        export_cdsr_subset(Path(args.cdsr_rdata), cd_ids, cdsr_csv)
        cdsr_df = pd.read_csv(cdsr_csv, dtype=str, keep_default_na=False)
    else:
        cdsr_df = pd.DataFrame()
    cdsr_df.to_csv(out_dir / "cdsr_package_review_subset.csv", index=False)

    ref_agg = aggregate_reference_evidence(refs_df)
    if not ref_agg.empty:
        ref_agg.to_csv(out_dir / "package_reference_evidence_by_study.csv", index=False)
    else:
        pd.DataFrame().to_csv(out_dir / "package_reference_evidence_by_study.csv", index=False)

    matches_df = build_matches(numeric_df, cdsr_df, ref_agg)
    effects_path = Path(args.effects)
    if effects_path.exists() and not matches_df.empty:
        effects_df = pd.read_csv(effects_path, dtype=str, keep_default_na=False)
        row_col = "Unnamed: 0" if "Unnamed: 0" in effects_df.columns else effects_df.columns[0]
        keep = [row_col]
        for col in ["study.id.sha1", "z", "RCT", "outcome.group", "outcome.nr", "comparison.nr"]:
            if col in effects_df.columns:
                keep.append(col)
        effects_keep = effects_df[keep].copy()
        effects_keep = effects_keep.rename(columns={row_col: "cochrane_effects_row"})
        effects_keep = effects_keep.rename(
            columns={
                "study.id.sha1": "effects_study_id_sha1",
                "z": "z_from_cochrane_effects_csv",
                "RCT": "RCT_from_cochrane_effects_csv",
                "outcome.group": "outcome_group_from_cochrane_effects_csv",
                "outcome.nr": "outcome_nr_from_cochrane_effects_csv",
                "comparison.nr": "comparison_nr_from_cochrane_effects_csv",
            }
        )
        matches_df = matches_df.merge(effects_keep, how="left", on="cochrane_effects_row")
        if "effects_study_id_sha1" in matches_df.columns:
            matches_df["study_id_sha1"] = matches_df["study_id_sha1"].where(
                matches_df["study_id_sha1"].astype(str).str.len() > 0,
                matches_df["effects_study_id_sha1"].fillna(""),
            )
    matches_df.to_csv(out_dir / "package_numeric_row_matches.csv", index=False)

    if not matches_df.empty:
        exact = matches_df[matches_df["match_status"] == "exact_raw_match"].copy()
        exact.to_csv(out_dir / "package_effect_provenance_pilot.csv", index=False)
        summary = (
            matches_df.groupby(["review_id", "match_status"], dropna=False)
            .size()
            .reset_index(name="n_package_rows")
            .sort_values(["review_id", "match_status"])
        )
        summary.to_csv(out_dir / "package_mapping_summary.csv", index=False)
    else:
        pd.DataFrame().to_csv(out_dir / "package_effect_provenance_pilot.csv", index=False)
        pd.DataFrame().to_csv(out_dir / "package_mapping_summary.csv", index=False)

    write_summary(out_dir / "package_probe_summary.md", manifests_df, studies_df, refs_df, numeric_df, cdsr_df, matches_df)

    print(f"Parsed {len(files)} package files")
    print(f"Studies: {len(studies_df)}")
    print(f"Numeric rows: {len(numeric_df)}")
    print(f"References: {len(refs_df)}")
    print(f"CDSR rows for these review IDs: {len(cdsr_df)}")
    if not matches_df.empty:
        print(matches_df["match_status"].value_counts(dropna=False).to_string())
    print(f"Wrote outputs to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
