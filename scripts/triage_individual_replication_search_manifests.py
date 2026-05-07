#!/usr/bin/env python3
"""Normalize and dedupe Figure 1 individual-replication search manifests."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SEARCH_DIR = ROOT / "steps" / "searches" / "figure1"
WORKLIST_DIR = ROOT / "steps" / "individual_replication_papers" / "figure1"
ROOT_PAIRS = ROOT / "FIGURE1_REPLICATION_PAIRS.tsv"
PAIR_BIBTEX = WORKLIST_DIR / "pair_chase" / "figure1-pair-bibtex-map.tsv"

ALL_CANDIDATES = WORKLIST_DIR / "individual-paper-search-intake-all.tsv"
TRIAGE = WORKLIST_DIR / "individual-paper-search-triage-batch001.tsv"
STRICT_WORKLIST = WORKLIST_DIR / "individual-paper-worklist-from-search.tsv"
D_EQ_WORKLIST = WORKLIST_DIR / "individual-paper-worklist-d-equivalent.tsv"
NATIVE_WORKLIST = WORKLIST_DIR / "individual-paper-worklist-native-only.tsv"
COVERAGE_WORKLIST = WORKLIST_DIR / "individual-paper-worklist-coverage-only.tsv"
REJECTIONS = WORKLIST_DIR / "individual-paper-search-rejections.tsv"
REPORT = ROOT / "reports" / "figure1_individual_replication_search_intake.md"
MANIFEST_GLOBS = ["individualrepsearch-*.json"]
PRIOR_SEED = Path("")

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

DOI_RE = re.compile(r"(10\.\d{4,9}/[^\s\"<>]+)", re.IGNORECASE)
ROUTE_ALIASES = {
    "strict": "strict_figure1a",
    "strict_d": "strict_figure1a",
    "strict_figure1a": "strict_figure1a",
    "figure1a": "strict_figure1a",
    "d_equivalent": "d_equivalent_figure1b",
    "d_equivalent_figure1b": "d_equivalent_figure1b",
    "figure1b": "d_equivalent_figure1b",
    "native": "native_only",
    "native_only": "native_only",
    "native_scale_subplot": "native_only",
    "native_scale": "native_only",
    "coverage": "coverage_only",
    "coverage_only": "coverage_only",
    "coverage_worklist": "coverage_only",
    "coverage_denominator": "coverage_only",
    "likely_exclude": "reject",
    "exclude": "reject",
    "reject": "reject",
}


def clean(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    text = str(value).replace("\t", " ").replace("\n", " ").replace("\r", " ").strip()
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
    return text.rstrip(".,);]").lower()


def norm_text(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", clean(value).lower()).strip()


def row_id(prefix: str, *parts: Any) -> str:
    payload = "||".join(clean(part) for part in parts)
    return f"{prefix}_{hashlib.sha1(payload.encode('utf-8')).hexdigest()[:16]}"


def as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [clean(v) for v in value if clean(v)]
    if isinstance(value, str):
        text = clean(value)
        if not text:
            return []
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return [clean(v) for v in parsed if clean(v)]
        except Exception:
            pass
        return [part.strip() for part in re.split(r"[|;]", text) if part.strip()]
    return [clean(value)] if clean(value) else []


def normalize_route(value: Any) -> str:
    route = clean(value).lower()
    return ROUTE_ALIASES.get(route, route)


def configure_batch(batch_id: str, manifest_globs: list[str], prior_seed: str = "") -> None:
    global TRIAGE, REPORT, MANIFEST_GLOBS, PRIOR_SEED
    TRIAGE = WORKLIST_DIR / f"individual-paper-search-triage-{batch_id}.tsv"
    REPORT = ROOT / "reports" / f"figure1_individual_replication_search_intake_{batch_id}.md"
    MANIFEST_GLOBS = manifest_globs or ["individualrepsearch-*.json"]
    PRIOR_SEED = ROOT / prior_seed if prior_seed else Path("")


def nested(candidate: dict[str, Any], side: str, field: str) -> str:
    obj = candidate.get(side)
    if isinstance(obj, dict):
        return clean(obj.get(field))
    return ""


def collect_urls(candidate: dict[str, Any]) -> list[str]:
    urls: list[str] = []
    urls.extend(as_list(candidate.get("source_object_urls")))
    urls.extend(as_list(candidate.get("source_object_urls_json")))
    for side in ["original", "replication_or_followup", "replication"]:
        obj = candidate.get(side)
        if isinstance(obj, dict):
            urls.extend(as_list(obj.get("source_object_urls")))
            for key in ["url", "doi", "pmcid", "pmid"]:
                value = clean(obj.get(key))
                if key == "doi" and norm_doi(value):
                    urls.append(f"https://doi.org/{norm_doi(value)}")
                elif key == "pmcid" and value:
                    urls.append(f"https://pmc.ncbi.nlm.nih.gov/articles/{value}/")
                elif key == "pmid" and value:
                    urls.append(f"https://pubmed.ncbi.nlm.nih.gov/{value}/")
                elif key == "url" and value:
                    urls.append(value)
    for item in candidate.get("source_objects_to_mirror_first") or []:
        if isinstance(item, dict):
            urls.append(clean(item.get("url")))
        else:
            urls.append(clean(item))
    out: list[str] = []
    seen = set()
    for url in urls:
        url = clean(url).strip("[]()")
        if not url or url in seen:
            continue
        out.append(url)
        seen.add(url)
    return out


def normalize_candidate(candidate: dict[str, Any], manifest_path: Path, index: int) -> dict[str, Any]:
    original_title = clean(candidate.get("original_title")) or nested(candidate, "original", "title")
    replication_title = (
        clean(candidate.get("replication_title"))
        or nested(candidate, "replication_or_followup", "title")
        or nested(candidate, "replication", "title")
    )
    original_doi = norm_doi(candidate.get("original_doi") or nested(candidate, "original", "doi"))
    replication_doi = norm_doi(
        candidate.get("replication_doi")
        or nested(candidate, "replication_or_followup", "doi")
        or nested(candidate, "replication", "doi")
    )
    value = candidate.get("value_availability") if isinstance(candidate.get("value_availability"), dict) else {}
    candidate_id = clean(candidate.get("candidate_id")) or row_id("candidate", manifest_path, index)
    conversion_route = clean(candidate.get("conversion_route")) or clean(value.get("conversion_route"))
    urls = collect_urls(candidate)
    dedupe_terms = as_list(candidate.get("dedupe_terms")) + [
        original_doi,
        replication_doi,
        original_title,
        replication_title,
        candidate_id,
    ]
    return {
        "manifest_path": str(manifest_path.relative_to(ROOT)),
        "candidate_index": index,
        "candidate_id": candidate_id,
        "candidate_name": clean(candidate.get("candidate_name")) or f"{original_title} -> {replication_title}".strip(" ->"),
        "domain": clean(candidate.get("domain")),
        "candidate_route": normalize_route(candidate.get("candidate_route")) or "coverage_only",
        "confidence": clean(candidate.get("confidence")) or "medium",
        "original_title": original_title,
        "original_doi": original_doi,
        "replication_title": replication_title,
        "replication_doi": replication_doi,
        "conversion_route": conversion_route,
        "dedupe_risk": clean(candidate.get("dedupe_risk")) or "medium",
        "source_object_urls_json": json.dumps(urls, ensure_ascii=True),
        "dedupe_terms_json": json.dumps([term for term in dedupe_terms if clean(term)], ensure_ascii=True),
        "relationship_evidence_json": json.dumps(candidate.get("relationship_evidence") or {}, ensure_ascii=True, sort_keys=True),
        "value_availability_json": json.dumps(value, ensure_ascii=True, sort_keys=True),
    }


def load_manifest(path: Path) -> list[dict[str, Any]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [
            {
                "candidate_id": row_id("manifest_parse_error", path),
                "candidate_name": f"Could not parse {path.name}",
                "candidate_route": "reject",
                "confidence": "low",
                "dedupe_risk": "low",
                "relationship_evidence": {"parse_error": str(exc)},
            }
        ]
    if isinstance(payload, list):
        candidates = payload
    elif isinstance(payload, dict):
        candidates = payload.get("candidates") or []
    else:
        candidates = []
    return [normalize_candidate(c, path, i) for i, c in enumerate(candidates, start=1) if isinstance(c, dict)]


def read_table(path: Path, sep: str = "\t") -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, sep=sep, dtype=str, keep_default_na=False)


def load_existing_pairs() -> pd.DataFrame:
    frames = []
    if ROOT_PAIRS.exists():
        frames.append(read_table(ROOT_PAIRS).assign(existing_table="FIGURE1_REPLICATION_PAIRS.tsv"))
    if PAIR_BIBTEX.exists():
        frames.append(read_table(PAIR_BIBTEX).assign(existing_table="figure1-pair-bibtex-map.tsv"))
    if not frames:
        return pd.DataFrame()
    out = pd.concat(frames, ignore_index=True, sort=False).fillna("")
    out["_dedupe_hay"] = out.astype(str).agg(" ".join, axis=1).str.lower()
    return out


def load_prior_seed() -> pd.DataFrame:
    if not PRIOR_SEED or not PRIOR_SEED.exists():
        return pd.DataFrame()
    seed = read_table(PRIOR_SEED).fillna("")
    seed["_dedupe_hay"] = seed.astype(str).agg(" ".join, axis=1).str.lower()
    return seed


def match_prior_seed(candidate: dict[str, Any], prior_seed: pd.DataFrame) -> pd.DataFrame:
    if prior_seed.empty:
        return prior_seed
    hay = prior_seed["_dedupe_hay"].astype(str)
    mask = pd.Series(False, index=prior_seed.index)
    candidate_id = clean(candidate.get("candidate_id"))
    if candidate_id and "candidate_id" in prior_seed.columns:
        mask |= prior_seed["candidate_id"].astype(str).eq(candidate_id)
    for value in [norm_doi(candidate.get("replication_doi")), norm_doi(candidate.get("original_doi"))]:
        if value:
            mask |= hay.str.contains(value, regex=False, na=False)
    for value in [norm_text(candidate.get("replication_title")), norm_text(candidate.get("original_title"))]:
        if len(value) >= 24:
            mask |= hay.str.contains(value, regex=False, na=False)
    return prior_seed[mask].copy()


def match_existing(candidate: dict[str, Any], existing: pd.DataFrame) -> pd.DataFrame:
    if existing.empty:
        return existing
    if "_dedupe_hay" in existing.columns:
        hay = existing["_dedupe_hay"].astype(str)
    else:
        hay = existing.astype(str).agg(" ".join, axis=1).str.lower()
    original_doi = norm_doi(candidate.get("original_doi"))
    replication_doi = norm_doi(candidate.get("replication_doi"))
    both_mask = pd.Series(False, index=existing.index)
    if original_doi and replication_doi:
        both_mask = hay.str.contains(original_doi, regex=False, na=False) & hay.str.contains(replication_doi, regex=False, na=False)
        if both_mask.any():
            return existing[both_mask].copy()
    one_mask = pd.Series(False, index=existing.index)
    if replication_doi:
        one_mask |= hay.str.contains(replication_doi, regex=False, na=False)
    if original_doi:
        one_mask |= hay.str.contains(original_doi, regex=False, na=False)
    if one_mask.any():
        return existing[one_mask].copy()
    terms = json.loads(candidate.get("dedupe_terms_json") or "[]")
    mask = pd.Series(False, index=existing.index)
    for term in terms:
        term = clean(term).lower()
        if len(term) < 8:
            continue
        mask |= hay.str.contains(term, regex=False, na=False)
    return existing[mask].copy()


def route_candidate(candidate: dict[str, Any], hits: pd.DataFrame, prior_hits: pd.DataFrame) -> tuple[str, str]:
    route = clean(candidate.get("candidate_route"))
    if route == "reject":
        return "reject", "Search manifest marked candidate as reject."
    if not prior_hits.empty:
        action_columns = [col for col in prior_hits.columns if col.endswith("_action")]
        actions = "|".join(
            sorted(
                {
                    clean(value)
                    for col in action_columns
                    for value in prior_hits[col].astype(str).tolist()
                    if clean(value)
                }
            )
        )
        return (
            "already_screened_prior_batch",
            f"Candidate matched prior batch closeout/dedupe seed; action={actions or 'prior_screened'}.",
        )
    if not hits.empty:
        fams = sorted(set(hits.get("source_family_key", pd.Series(dtype=str)).astype(str).replace("", pd.NA).dropna()))
        pair_ids = sorted(set(hits.get("figure1_replication_pair_id", pd.Series(dtype=str)).astype(str).replace("", pd.NA).dropna()))
        if pair_ids:
            return (
                "already_in_root_table",
                "Local dedupe found DOI/title/source-family evidence in current Figure 1 pair maps; keep as duplicate/search-recall evidence unless outcome-level review shows a genuinely new contrast.",
            )
        return (
            "possible_existing_source_overlap",
            f"Matched existing source-side identity but no root pair ID in the hit table; likely overlap families: {'|'.join(fams)}.",
        )
    if route == "strict_figure1a":
        return "route_to_individual_strict_extraction", "No local pair match; queue for source-object mirroring and strict D/N extraction."
    if route == "d_equivalent_figure1b":
        return "route_to_individual_d_equivalent_extraction", "No local pair match; queue for D-equivalent binary/clinical extraction."
    if route == "native_only":
        return "route_to_native_only_extraction", "No local pair match; queue for native-scale retention."
    if route == "coverage_only":
        return "route_to_coverage_only", "No local pair match; retain as source-object coverage denominator until values are found."
    return "needs_route_review", f"Unknown candidate_route={route}."


def worklist_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "worklist_task_id": row_id("individual_search_task", row["candidate_id"], row["route_decision"]),
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


def write() -> None:
    SEARCH_DIR.mkdir(parents=True, exist_ok=True)
    WORKLIST_DIR.mkdir(parents=True, exist_ok=True)
    manifests: list[Path] = []
    for pattern in MANIFEST_GLOBS:
        manifests.extend(sorted(SEARCH_DIR.glob(pattern)))
    manifests = sorted(set(manifests))
    manifests = [p for p in manifests if "candidate-schema" not in p.name]
    existing = load_existing_pairs()
    prior_seed = load_prior_seed()
    created_at = datetime.now(timezone.utc).isoformat()
    candidates: list[dict[str, Any]] = []
    for path in manifests:
        candidates.extend(load_manifest(path))
    deduped: dict[str, dict[str, Any]] = {}
    for cand in candidates:
        deduped.setdefault(clean(cand["candidate_id"]) or row_id("candidate", len(deduped)), cand)
    triage_rows = []
    for cand in deduped.values():
        hits = match_existing(cand, existing)
        prior_hits = match_prior_seed(cand, prior_seed)
        decision, reason = route_candidate(cand, hits, prior_hits)
        root_ids = "|".join(sorted(set(hits.get("figure1_replication_pair_id", pd.Series(dtype=str)).astype(str).replace("", pd.NA).dropna().tolist())))
        fams = "|".join(sorted(set(hits.get("source_family_key", pd.Series(dtype=str)).astype(str).replace("", pd.NA).dropna().tolist())))
        row = dict(cand)
        row.update(
            {
                "local_match_count": len(hits),
                "prior_seed_match_count": len(prior_hits),
                "matched_root_pair_ids": root_ids,
                "matched_source_family_keys": fams,
                "route_decision": decision,
                "route_reason": reason,
                "created_at": created_at,
            }
        )
        triage_rows.append(row)

    triage = pd.DataFrame(triage_rows).fillna("")
    triage.to_csv(ALL_CANDIDATES, sep="\t", index=False)
    triage.to_csv(TRIAGE, sep="\t", index=False)

    strict = [worklist_row(r) for r in triage_rows if r["route_decision"] == "route_to_individual_strict_extraction"]
    deq = [worklist_row(r) for r in triage_rows if r["route_decision"] == "route_to_individual_d_equivalent_extraction"]
    native = [worklist_row(r) for r in triage_rows if r["route_decision"] == "route_to_native_only_extraction"]
    coverage = [worklist_row(r) for r in triage_rows if r["route_decision"] == "route_to_coverage_only"]
    rejected = [
        {
            "rejection_id": row_id("individual_search_reject", r["candidate_id"], r["route_decision"]),
            "candidate_id": r["candidate_id"],
            "candidate_name": r["candidate_name"],
            "route_decision": r["route_decision"],
            "reason": r["route_reason"],
            "matched_root_pair_ids": r["matched_root_pair_ids"],
            "matched_source_family_keys": r["matched_source_family_keys"],
            "created_at": r["created_at"],
        }
        for r in triage_rows
        if r["route_decision"] not in {
            "route_to_individual_strict_extraction",
            "route_to_individual_d_equivalent_extraction",
            "route_to_native_only_extraction",
            "route_to_coverage_only",
        }
    ]
    pd.DataFrame(strict, columns=WORKLIST_COLUMNS).fillna("").to_csv(STRICT_WORKLIST, sep="\t", index=False)
    pd.DataFrame(deq, columns=WORKLIST_COLUMNS).fillna("").to_csv(D_EQ_WORKLIST, sep="\t", index=False)
    pd.DataFrame(native, columns=WORKLIST_COLUMNS).fillna("").to_csv(NATIVE_WORKLIST, sep="\t", index=False)
    pd.DataFrame(coverage, columns=WORKLIST_COLUMNS).fillna("").to_csv(COVERAGE_WORKLIST, sep="\t", index=False)
    pd.DataFrame(rejected, columns=REJECTION_COLUMNS).fillna("").to_csv(REJECTIONS, sep="\t", index=False)

    counts = triage["route_decision"].value_counts().to_dict() if not triage.empty else {}
    lines = [
        "# Figure 1 Individual Replication Search Intake",
        "",
        f"- Manifests read: {len(manifests):,}",
        f"- Unique candidates: {len(triage):,}",
        f"- New strict Figure 1A candidates: {counts.get('route_to_individual_strict_extraction', 0):,}",
        f"- New D-equivalent candidates: {counts.get('route_to_individual_d_equivalent_extraction', 0):,}",
        f"- New native-only candidates: {counts.get('route_to_native_only_extraction', 0):,}",
        f"- Coverage-only candidates: {counts.get('route_to_coverage_only', 0):,}",
        f"- Duplicate/possible-overlap/rejected candidates: {len(rejected):,}",
        "",
        "## Route Counts",
        "",
    ]
    for key, value in sorted(counts.items()):
        lines.append(f"- {key}: {value:,}")
    lines.extend(
        [
            "",
            "## Outputs",
            "",
            f"- `{ALL_CANDIDATES.relative_to(ROOT)}`",
            f"- `{STRICT_WORKLIST.relative_to(ROOT)}`",
            f"- `{D_EQ_WORKLIST.relative_to(ROOT)}`",
            f"- `{NATIVE_WORKLIST.relative_to(ROOT)}`",
            f"- `{COVERAGE_WORKLIST.relative_to(ROOT)}`",
            f"- `{REJECTIONS.relative_to(ROOT)}`",
        ]
    )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {TRIAGE} ({len(triage)} candidates)")
    print(f"Wrote {STRICT_WORKLIST} ({len(strict)} strict rows)")
    print(f"Wrote {REPORT}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-id", default="batch001")
    parser.add_argument(
        "--manifest-glob",
        action="append",
        default=[],
        help="Manifest glob relative to steps/searches/figure1. Repeat for multiple globs.",
    )
    parser.add_argument(
        "--prior-seed",
        default="",
        help="Repo-relative TSV of previously screened candidates to skip before mirroring.",
    )
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()
    configure_batch(args.batch_id, args.manifest_glob or ["individualrepsearch-*.json"], args.prior_seed)
    write()


if __name__ == "__main__":
    main()
