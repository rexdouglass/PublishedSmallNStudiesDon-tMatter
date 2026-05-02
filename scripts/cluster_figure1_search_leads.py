#!/usr/bin/env python3
"""Cluster Figure 1 search leads into source-family review groups.

This is a read-only bridge step between broad discovery and review. It consumes
the root corpus/database table, saved ``corporasearch-*`` manifests, the active
review cue, and review receipts. It writes target artifacts that make aliasing,
source-family grouping, and priority review explicit.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MASTER_TSV = ROOT / "CORPORA_AND_DATABASES.tsv"
SEARCH_DIR = ROOT / "steps" / "searches" / "figure1"
REVIEW_ROOT = ROOT / "steps" / "review_cue" / "figure1_search_leads"
QUEUE_JSON = REVIEW_ROOT / "reviewcue-queue-figure1_search_leads.json"
RECEIPTS_ROOT = REVIEW_ROOT / "receipts"
CLUSTER_RECEIPTS_ROOT = REVIEW_ROOT / "cluster_receipts"

CLUSTERS_JSON = SEARCH_DIR / "alias-clusters-leads-artifacts-root-v001.json"
PRIORITY_QUEUE_TSV = REVIEW_ROOT / "clustered-priority-queue.tsv"
PRIORITY_SUMMARY_TSV = REVIEW_ROOT / "clustered-priority-queue-summary.tsv"

DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.I)

GENERIC_TITLE_KEYS = {
    "",
    ".",
    "data",
    "dataset",
    "code",
    "materials",
    "replication",
    "replication_data",
    "replication_package",
    "registered_replication_report",
    "registered_report",
    "original",
    "original_study",
    "replication_study",
    "direct_replication",
    "study_1_direct_replication",
    "study_2_direct_replication",
    "0_master",
    "codebook",
    "templates",
    "variables",
    "get_data",
    "metaanalysis",
    "osf_manifest",
    "osf_file_list",
    "osf_file_manifest",
    "github_contents_manifest",
    "github_contents_file_list",
    "original_data",
    "finaldata",
}

SOURCE_OBJECT_TERMS = [
    "database",
    "dataset",
    "data set",
    "data file",
    "csv",
    "xlsx",
    "xls",
    "rds",
    "stata",
    "spss",
    "sav",
    "dta",
    "json",
    "source data",
    "supplementary data",
    "repository",
    "osf",
    "dataverse",
    "zenodo",
    "dryad",
    "figshare",
    "icpsr",
    "github",
    "code and data",
    "download",
    "file inventory",
    "workbook",
    "table",
]

PAIR_EVIDENCE_TERMS = [
    "original and replication",
    "original finding",
    "replication finding",
    "original effect",
    "replication effect",
    "original_effect",
    "replication_effect",
    "original n",
    "replication n",
    "original_n",
    "replication_n",
    "original sample size",
    "replication sample size",
    "study_pair_id",
    "paired findings",
    "claim-replication",
    "direct replication",
    "registered replication",
    "multi-lab replication",
    "multilab replication",
    "reproducibility project",
    "replication project",
]

LOW_VALUE_CONTEXT_TERMS = [
    "comment on",
    "editorial",
    "tutorial",
    "scoping review",
    "systematic review",
    "forecasting",
    "sample size planning",
    "power analysis",
    "metrics to quantify",
]

FAMILY_HINT_PATTERNS = [
    ("fred", [r"\bforrt\b.*\breplication database\b", r"\bfred\b", r"\breplications and reversals\b"]),
    ("score", [r"\bdarpa score\b", r"\bsystematizing confidence\b", r"\bcredibility assessments?\b"]),
    ("rpp", [r"\breproducibility project[: -]+psychology\b", r"\bestimating the reproducibility of psychological science\b"]),
    ("rpcb", [r"\breproducibility project[: -]+cancer biology\b", r"\brp[_ -]?cb\b", r"\brpcb\b", r"\bpreclinical cancer biology\b"]),
    ("many_labs", [r"\bmany labs\b", r"\bmanylabs\b"]),
    ("many_babies", [r"\bmany babies\b", r"\bmanybabies\b"]),
    ("many_primates", [r"\bmany primates\b", r"\bmanyprimates\b"]),
    ("ssrp", [r"\bsocial science replication project\b"]),
    ("eerp", [r"\bexperimental economics replication project\b"]),
    ("loopr", [r"\bloopr\b"]),
    ("psa", [r"\bpsychological science accelerator\b"]),
    ("msrp", [r"\bmulti[- ]?site registered replication\b", r"\bmsrp\b"]),
]


def safe_text(value: object, max_len: int = 12000) -> str:
    if value is None:
        return ""
    text = str(value).replace("\t", " ")
    return re.sub(r"\s+", " ", text).strip()[:max_len]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def repo_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def slugify(value: object, fallback: str = "item") -> str:
    text = unicodedata.normalize("NFKD", safe_text(value))
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return slug[:180] or fallback


def stable_id(prefix: str, *parts: object) -> str:
    text = "\n".join(safe_text(part, max_len=20000) for part in parts)
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
    label = slugify(next((part for part in parts if safe_text(part)), prefix), prefix)[:80]
    return f"{prefix}_{label}_{digest}"


def split_values(value: object) -> list[str]:
    text = safe_text(value)
    if not text:
        return []
    return [part for part in (safe_text(part) for part in re.split(r"\s*\|\s*|\s*;\s*", text)) if part]


def normalize_doi(value: object) -> str:
    text = safe_text(value)
    if not text:
        return ""
    text = re.sub(r"^doi:\s*", "", text, flags=re.I)
    text = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", text, flags=re.I)
    match = DOI_RE.search(text)
    if not match:
        return ""
    return match.group(0).rstrip(".,;)").lower()


def normalize_url(value: object) -> str:
    text = safe_text(value)
    if not text:
        return ""
    candidates = split_values(text)
    url = candidates[0] if candidates else text
    if not url.startswith(("http://", "https://")):
        return ""
    url = re.sub(r"^https?://dx\.doi\.org/", "https://doi.org/", url, flags=re.I)
    url = re.sub(r"#.*$", "", url)
    url = re.sub(r"\?.*$", "", url)
    return url.rstrip("/").lower()


def title_key(value: object) -> str:
    key = slugify(value, "")
    if len(key) < 12 or key in GENERIC_TITLE_KEYS:
        return ""
    generic_patterns = [
        r"^github_\d+(_|$)",
        r"^osf_\d+_(download|readme|rename|quick|manual|power|finaldata)",
        r"^\d{3}_(full|pilot)_10_",
        r"^\d{6}$",
        r"^article_\d+$",
        r"^rp_cb_final_analysis_(paper|experiment|effect)_level_data(_dictionary)?$",
    ]
    if any(re.search(pattern, key) for pattern in generic_patterns):
        return ""
    return key


def extract_osf_guids(*values: object) -> set[str]:
    out: set[str] = set()
    for value in values:
        text = safe_text(value)
        for match in re.finditer(r"(?:osf:|osf\.io/)([a-z0-9]{5,8})", text, flags=re.I):
            out.add(match.group(1).lower())
        for part in split_values(text):
            if re.fullmatch(r"[a-z0-9]{5}", part, flags=re.I):
                out.add(part.lower())
    return out


def extract_github_repo(*values: object) -> str:
    for value in values:
        text = safe_text(value)
        match = re.search(r"github\.com/([^/\s]+)/([^/\s#?]+)", text, flags=re.I)
        if match:
            return f"{match.group(1).lower()}/{match.group(2).lower().removesuffix('.git')}"
    return ""


def local_family_key(*values: object) -> str:
    for value in values:
        text = safe_text(value)
        for part in split_values(text) or [text]:
            path = Path(part)
            pieces = path.parts
            if len(pieces) >= 3 and pieces[0] == "data" and pieces[1] == "raw" and pieces[2] == "corpus_candidates":
                if len(pieces) >= 4:
                    return f"raw_corpus:{pieces[3].lower()}"
            if len(pieces) >= 3 and pieces[0] == "data" and pieces[1] == "raw" and pieces[2] == "replication_projects":
                if len(pieces) >= 5 and pieces[3] == "lead_harvest":
                    return f"lead_harvest:{pieces[4].lower()}"
                if len(pieces) >= 4:
                    return f"raw_replication_project:{pieces[3].lower()}"
            if len(pieces) >= 5 and pieces[:4] == ("data", "derived", "replication_pairs", "harvest"):
                return f"derived_replication_pairs:{Path(part).stem.lower().replace('__promoted_pairs', '')}"
    return ""


def family_hints(row: dict[str, str]) -> list[str]:
    text = " ".join(
        safe_text(row.get(field, ""))
        for field in ["name", "description", "why_relevant", "source_family", "source_key", "landing_url", "local_raw_paths", "backing_files", "notes"]
    ).lower()
    hints: list[str] = []
    for family, patterns in FAMILY_HINT_PATTERNS:
        if any(re.search(pattern, text, flags=re.I) for pattern in patterns):
            hints.append(family)
    return hints


def evidence_score(row: dict[str, str], terms: list[str]) -> int:
    text = " ".join(
        safe_text(row.get(field, ""))
        for field in ["name", "description", "why_relevant", "source_key", "landing_url", "raw_url", "local_raw_paths", "backing_files", "notes"]
    ).lower()
    return sum(1 for term in terms if term in text)


def source_object_score(row: dict[str, str]) -> int:
    score = evidence_score(row, SOURCE_OBJECT_TERMS)
    if row.get("record_kind") in {"candidate_repository_package", "candidate_result_table"}:
        score += 3
    if row.get("host") in {"osf.io", "dataverse.harvard.edu", "doi.org", "github.com"}:
        score += 1
    for field in ["landing_url", "raw_url", "local_raw_paths", "backing_files"]:
        if re.search(r"\.(csv|tsv|xlsx|xls|rds|rdata|sav|dta|json|zip)(?:$|\b)", safe_text(row.get(field, "")), flags=re.I):
            score += 3
    return score


def pair_score(row: dict[str, str]) -> int:
    score = evidence_score(row, PAIR_EVIDENCE_TERMS)
    if row.get("has_replication_pair_mapping") == "yes":
        score += 4
    if row.get("figure1_replication_relevance") == "yes":
        score += 1
    return score


def context_penalty(row: dict[str, str]) -> int:
    text = f"{row.get('name', '')} {row.get('description', '')}".lower()
    penalty = sum(2 for term in LOW_VALUE_CONTEXT_TERMS if term in text)
    if row.get("record_kind") in {"candidate_context_or_methods_paper", "candidate_bibliographic_paper"}:
        penalty += 3
    if row.get("inventory_status") in {"rejected_irrelevant_search_hit", "catalog_only_context_lead"}:
        penalty += 8
    if row.get("inventory_status") == "routed_to_individual_paper_search":
        penalty += 4
    return penalty


class UnionFind:
    def __init__(self) -> None:
        self.parent: dict[str, str] = {}

    def add(self, item: str) -> None:
        self.parent.setdefault(item, item)

    def find(self, item: str) -> str:
        self.add(item)
        if self.parent[item] != item:
            self.parent[item] = self.find(self.parent[item])
        return self.parent[item]

    def union(self, a: str, b: str) -> None:
        ra = self.find(a)
        rb = self.find(b)
        if ra != rb:
            self.parent[rb] = ra


def load_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return [{key: safe_text(value) for key, value in row.items()} for row in reader]


def manifest_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in sorted(SEARCH_DIR.glob("corporasearch-*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        for bucket in ["candidates", "routed_or_rejected_leads"]:
            for item in payload.get(bucket, []):
                if not isinstance(item, dict):
                    continue
                row = {key: safe_text(value) for key, value in item.items()}
                row["manifest_path"] = repo_path(path)
                row["manifest_bucket"] = bucket
                row["node_source"] = "search_manifest"
                rows.append(row)
    return rows


def queue_index() -> dict[str, dict[str, str]]:
    if not QUEUE_JSON.exists():
        return {}
    payload = json.loads(QUEUE_JSON.read_text(encoding="utf-8"))
    out: dict[str, dict[str, str]] = {}
    for item in payload.get("queue", []):
        if not isinstance(item, dict):
            continue
        row = {key: safe_text(value) for key, value in item.items()}
        for key in [row.get("lead_key"), row.get("review_id"), row.get("corpus_database_id")]:
            if key:
                out[key] = row
    return out


def receipt_index() -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    if not RECEIPTS_ROOT.exists():
        return out
    for path in RECEIPTS_ROOT.glob("*/*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        row = {key: safe_text(value) for key, value in payload.items()}
        row["receipt_path"] = repo_path(path)
        for key in [row.get("lead_key"), row.get("review_id"), row.get("canonical_source_key")]:
            if key:
                out[key] = row
    return out


def cluster_receipt_index() -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    if not CLUSTER_RECEIPTS_ROOT.exists():
        return out
    for path in CLUSTER_RECEIPTS_ROOT.glob("*/*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        cluster_id = safe_text(payload.get("cluster_id"))
        if not cluster_id:
            continue
        row = {
            "cluster_review_decision": safe_text(payload.get("decision")),
            "cluster_review_parent_key": safe_text(payload.get("parent_corpus_database_id_or_key")),
            "cluster_review_receipt_path": repo_path(path),
        }
        out[cluster_id] = row
    return out


def make_node(row: dict[str, str], source: str, source_path: str, index: int) -> dict[str, Any]:
    lead_key = row.get("lead_key") or (f"title:{title_key(row.get('name'))}" if title_key(row.get("name")) else "")
    node_id = stable_id("node", source, source_path, row.get("corpus_database_id"), lead_key, row.get("source_key"), row.get("landing_url"), row.get("name"), index)
    out = dict(row)
    out.update(
        {
            "node_id": node_id,
            "node_source": source,
            "source_path": source_path,
            "lead_key": lead_key,
            "source_object_score": str(source_object_score(row)),
            "pair_evidence_score": str(pair_score(row)),
            "context_penalty": str(context_penalty(row)),
            "family_hints": " | ".join(family_hints(row)),
        }
    )
    return out


def node_keys(node: dict[str, Any]) -> list[tuple[str, str, str]]:
    row = {key: safe_text(value) for key, value in node.items()}
    keys: list[tuple[str, str, str]] = []
    for field in ["source_key", "landing_url", "raw_url", "notes"]:
        doi = normalize_doi(row.get(field))
        if doi:
            keys.append(("exact_doi", f"doi:{doi}", "strict"))
    for field in ["landing_url", "raw_url"]:
        url = normalize_url(row.get(field))
        if url:
            keys.append(("normalized_url", f"url:{url}", "strict"))
    for guid in extract_osf_guids(row.get("source_key"), row.get("landing_url"), row.get("raw_url"), row.get("notes")):
        keys.append(("osf_guid", f"osf:{guid}", "strict"))
    github = extract_github_repo(row.get("landing_url"), row.get("raw_url"), row.get("description"), row.get("notes"))
    if github:
        keys.append(("github_repo", f"github:{github}", "strict"))
    local_family = local_family_key(row.get("landing_url"), row.get("raw_url"), row.get("local_raw_paths"), row.get("backing_files"), row.get("source_key"))
    if local_family:
        keys.append(("local_path_family", local_family, "strict"))
    title = title_key(row.get("name"))
    if title:
        keys.append(("exact_title", f"title:{title}", "strict"))
    return list(dict.fromkeys(keys))


def build_nodes() -> list[dict[str, Any]]:
    qidx = queue_index()
    ridx = receipt_index()
    nodes: list[dict[str, Any]] = []
    for idx, row in enumerate(load_tsv(MASTER_TSV)):
        row["manifest_path"] = row.get("discovery_source_path", "")
        row["manifest_bucket"] = "root_table"
        node = make_node(row, "root_table", repo_path(MASTER_TSV), idx)
        nodes.append(node)
    offset = len(nodes)
    for idx, row in enumerate(manifest_rows(), start=offset):
        node = make_node(row, "search_manifest", row.get("manifest_path", ""), idx)
        nodes.append(node)

    for node in nodes:
        for key in [safe_text(node.get("lead_key")), safe_text(node.get("review_id")), safe_text(node.get("corpus_database_id"))]:
            if key and key in qidx:
                node["review_queue_status"] = qidx[key].get("triage_queue_status", "needs_review")
                node["review_id"] = node.get("review_id") or qidx[key].get("review_id", "")
                break
        else:
            node["review_queue_status"] = ""
        for key in [safe_text(node.get("lead_key")), safe_text(node.get("review_id")), safe_text(node.get("source_key"))]:
            if key and key in ridx:
                receipt = ridx[key]
                node["review_decision"] = receipt.get("decision", "")
                node["review_receipt_path"] = receipt.get("receipt_path", "")
                node["canonical_source_key"] = receipt.get("canonical_source_key", "")
                break
        else:
            node["review_decision"] = ""
            node["review_receipt_path"] = ""
            node["canonical_source_key"] = ""
    return nodes


def cluster_priority(nodes: list[dict[str, Any]], edge_types: set[str]) -> tuple[int, str, str]:
    source_score = max((int(node.get("source_object_score") or 0) for node in nodes), default=0)
    pair_evidence = max((int(node.get("pair_evidence_score") or 0) for node in nodes), default=0)
    penalty = min((int(node.get("context_penalty") or 0) for node in nodes), default=0)
    open_review = sum(1 for node in nodes if node.get("review_queue_status") in {"needs_review", "needs_root_candidate_review"})
    reviewed = sum(1 for node in nodes if node.get("review_decision"))
    root_candidate = sum(1 for node in nodes if node.get("node_source") == "root_table")
    candidate_kind = sum(1 for node in nodes if node.get("record_kind") in {"candidate_corpus_or_database", "candidate_repository_package", "candidate_result_table"})
    score = source_score * 4 + pair_evidence * 5 + min(open_review, 5) * 5 + min(candidate_kind, 5) * 2 + min(root_candidate, 3) - penalty * 3 - min(reviewed, 5)
    if score >= 45:
        band = "high"
    elif score >= 25:
        band = "medium"
    else:
        band = "low"
    if open_review and band in {"high", "medium"}:
        action = "review_cluster_representative"
    elif reviewed:
        action = "skip_reviewed_or_use_receipt"
    elif source_score >= 4 and pair_evidence >= 3:
        action = "inventory_source_family_artifacts"
    else:
        action = "deprioritize_or_context_review"
    return score, band, action


def representative_name_for(nodes: list[dict[str, Any]], shared_keys: list[str]) -> str:
    def good_name(node: dict[str, Any]) -> str:
        name = safe_text(node.get("name"))
        return name if title_key(name) else ""

    root_names = [good_name(node) for node in nodes if node.get("node_source") == "root_table"]
    root_names = [name for name in root_names if name]
    if root_names:
        return sorted(root_names, key=lambda value: (len(value), value.lower()))[0]

    non_table_names = [
        good_name(node)
        for node in nodes
        if node.get("record_kind") not in {"candidate_result_table"}
    ]
    non_table_names = [name for name in non_table_names if name]
    if non_table_names:
        return sorted(non_table_names, key=lambda value: (len(value), value.lower()))[0]

    good_names = [good_name(node) for node in nodes]
    good_names = [name for name in good_names if name]
    if good_names:
        return sorted(good_names, key=lambda value: (len(value), value.lower()))[0]

    family_keys = [key for key in shared_keys if key.startswith(("raw_corpus:", "raw_replication_project:", "lead_harvest:", "github:"))]
    if family_keys:
        label = family_keys[0].split(":", 1)[1]
        return label.replace("_", " ").replace("/", " / ").title()

    names = [safe_text(node.get("name")) for node in nodes if safe_text(node.get("name"))]
    return sorted(names, key=lambda value: (len(value) < 8, len(value), value.lower()))[0] if names else "unnamed cluster"


def build_clusters(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cluster_receipts = cluster_receipt_index()
    uf = UnionFind()
    key_to_nodes: dict[str, list[str]] = defaultdict(list)
    key_types: dict[str, tuple[str, str]] = {}
    node_by_id = {node["node_id"]: node for node in nodes}
    for node in nodes:
        uf.add(node["node_id"])
        for edge_type, key, strength in node_keys(node):
            key_to_nodes[key].append(node["node_id"])
            key_types[key] = (edge_type, strength)

    for key, ids in key_to_nodes.items():
        if len(ids) < 2:
            continue
        first = ids[0]
        for other in ids[1:]:
            uf.union(first, other)

    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for node in nodes:
        groups[uf.find(node["node_id"])].append(node)

    node_to_keys = defaultdict(list)
    for key, ids in key_to_nodes.items():
        if len(ids) < 2:
            continue
        for node_id in ids:
            node_to_keys[node_id].append(key)

    clusters: list[dict[str, Any]] = []
    for group_nodes in groups.values():
        shared_keys: list[str] = []
        edge_types: set[str] = set()
        strengths: set[str] = set()
        for node in group_nodes:
            for key in node_to_keys[node["node_id"]]:
                if key not in shared_keys:
                    shared_keys.append(key)
                    edge_type, strength = key_types[key]
                    edge_types.add(edge_type)
                    strengths.add(strength)
        family_counts = Counter()
        for node in group_nodes:
            for hint in split_values(node.get("family_hints", "")):
                family_counts[hint] += 1
        strict_keys = [key for key in shared_keys if key_types.get(key, ("", ""))[1] == "strict"]
        review_keys = [key for key in shared_keys if key_types.get(key, ("", ""))[1] == "review"]
        representative = representative_name_for(group_nodes, shared_keys)
        score, band, action = cluster_priority(group_nodes, edge_types)
        record_kinds = Counter(safe_text(node.get("record_kind")) for node in group_nodes if safe_text(node.get("record_kind")))
        statuses = Counter(safe_text(node.get("inventory_status")) for node in group_nodes if safe_text(node.get("inventory_status")))
        decisions = Counter(safe_text(node.get("review_decision")) for node in group_nodes if safe_text(node.get("review_decision")))
        manifests = sorted({safe_text(node.get("manifest_path")) for node in group_nodes if safe_text(node.get("manifest_path"))})
        cluster_id = stable_id("cluster", representative, "|".join(sorted(shared_keys)) or "|".join(sorted(node["node_id"] for node in group_nodes)))
        cluster_receipt = cluster_receipts.get(cluster_id, {})
        if cluster_receipt:
            action = "skip_cluster_reviewed_or_use_cluster_receipt"
        clusters.append(
            {
                "cluster_id": cluster_id,
                "representative_name": representative,
                "priority_score": score,
                "priority_band": band,
                "recommended_next_action": action,
                "cluster_review_decision": cluster_receipt.get("cluster_review_decision", ""),
                "cluster_review_receipt_path": cluster_receipt.get("cluster_review_receipt_path", ""),
                "cluster_review_parent_key": cluster_receipt.get("cluster_review_parent_key", ""),
                "cluster_confidence": "strict" if strict_keys else ("review" if review_keys else "singleton"),
                "preferred_family_hint": family_counts.most_common(1)[0][0] if family_counts else "",
                "node_count": len(group_nodes),
                "root_row_count": sum(1 for node in group_nodes if node.get("node_source") == "root_table"),
                "search_lead_count": sum(1 for node in group_nodes if node.get("node_source") == "search_manifest"),
                "open_review_count": sum(1 for node in group_nodes if node.get("review_queue_status") in {"needs_review", "needs_root_candidate_review"}),
                "receipt_count": sum(1 for node in group_nodes if node.get("review_decision")),
                "max_source_object_score": max((int(node.get("source_object_score") or 0) for node in group_nodes), default=0),
                "max_pair_evidence_score": max((int(node.get("pair_evidence_score") or 0) for node in group_nodes), default=0),
                "strict_keys": strict_keys,
                "review_keys": review_keys,
                "record_kind_counts": dict(record_kinds),
                "inventory_status_counts": dict(statuses),
                "review_decision_counts": dict(decisions),
                "manifest_paths": manifests,
                "nodes": sorted(group_nodes, key=lambda node: (node.get("node_source", ""), node.get("name", ""), node.get("landing_url", ""))),
            }
        )
    return sorted(clusters, key=lambda cluster: (-cluster["priority_score"], cluster["representative_name"].lower()))


def write_json(path: Path, payload: dict[str, Any], replace: bool) -> bool:
    if path.exists() and not replace:
        print(f"Skipped {repo_path(path)} because it exists. Use --replace to rebuild.")
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Wrote {repo_path(path)}")
    return True


def write_tsv(path: Path, rows: list[dict[str, str]], columns: list[str], replace: bool) -> bool:
    if path.exists() and not replace:
        print(f"Skipped {repo_path(path)} because it exists. Use --replace to rebuild.")
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {repo_path(path)}")
    return True


def priority_rows(clusters: list[dict[str, Any]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for cluster in clusters:
        rows.append(
            {
                "cluster_id": cluster["cluster_id"],
                "priority_band": cluster["priority_band"],
                "priority_score": str(cluster["priority_score"]),
                "recommended_next_action": cluster["recommended_next_action"],
                "cluster_confidence": cluster["cluster_confidence"],
                "representative_name": cluster["representative_name"],
                "preferred_family_hint": cluster["preferred_family_hint"],
                "node_count": str(cluster["node_count"]),
                "root_row_count": str(cluster["root_row_count"]),
                "search_lead_count": str(cluster["search_lead_count"]),
                "open_review_count": str(cluster["open_review_count"]),
                "receipt_count": str(cluster["receipt_count"]),
                "cluster_review_decision": cluster.get("cluster_review_decision", ""),
                "cluster_review_receipt_path": cluster.get("cluster_review_receipt_path", ""),
                "cluster_review_parent_key": cluster.get("cluster_review_parent_key", ""),
                "max_source_object_score": str(cluster["max_source_object_score"]),
                "max_pair_evidence_score": str(cluster["max_pair_evidence_score"]),
                "record_kind_counts": " | ".join(f"{key}={value}" for key, value in sorted(cluster["record_kind_counts"].items())),
                "inventory_status_counts": " | ".join(f"{key}={value}" for key, value in sorted(cluster["inventory_status_counts"].items())),
                "review_decision_counts": " | ".join(f"{key}={value}" for key, value in sorted(cluster["review_decision_counts"].items())),
                "strict_keys": " | ".join(cluster["strict_keys"][:12]),
                "review_keys": " | ".join(cluster["review_keys"][:12]),
                "manifest_paths": " | ".join(cluster["manifest_paths"][:8]),
                "example_node_names": " | ".join(
                    dict.fromkeys(safe_text(node.get("name")) for node in cluster["nodes"] if safe_text(node.get("name")))
                )[:1200],
            }
        )
    return rows


def summary_rows(clusters: list[dict[str, Any]]) -> list[dict[str, str]]:
    counters = {
        "priority_band": Counter(cluster["priority_band"] for cluster in clusters),
        "cluster_confidence": Counter(cluster["cluster_confidence"] for cluster in clusters),
        "recommended_next_action": Counter(cluster["recommended_next_action"] for cluster in clusters),
    }
    rows: list[dict[str, str]] = []
    for metric, counter in counters.items():
        for value, count in sorted(counter.items()):
            rows.append({"metric": metric, "value": value, "cluster_count": str(count)})
    rows.append({"metric": "total", "value": "clusters", "cluster_count": str(len(clusters))})
    rows.append({"metric": "total", "value": "nodes", "cluster_count": str(sum(cluster["node_count"] for cluster in clusters))})
    rows.append({"metric": "total", "value": "open_review_nodes", "cluster_count": str(sum(cluster["open_review_count"] for cluster in clusters))})
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replace", action="store_true", help="Replace existing cluster artifacts.")
    args = parser.parse_args()

    targets = [CLUSTERS_JSON, PRIORITY_QUEUE_TSV, PRIORITY_SUMMARY_TSV]
    if any(path.exists() for path in targets) and not args.replace:
        existing = ", ".join(repo_path(path) for path in targets if path.exists())
        print(f"Skipped because cluster output exists: {existing}. Use --replace to rerun.")
        return

    nodes = build_nodes()
    clusters = build_clusters(nodes)
    payload = {
        "created_at": utc_now(),
        "inputs": {
            "root_table": repo_path(MASTER_TSV),
            "search_glob": "steps/searches/figure1/corporasearch-*.json",
            "review_queue": repo_path(QUEUE_JSON),
            "receipts_root": repo_path(RECEIPTS_ROOT),
            "cluster_receipts_root": repo_path(CLUSTER_RECEIPTS_ROOT),
        },
        "cluster_count": len(clusters),
        "node_count": len(nodes),
        "clusters": clusters,
    }
    write_json(CLUSTERS_JSON, payload, args.replace)
    write_tsv(
        PRIORITY_QUEUE_TSV,
        priority_rows(clusters),
        [
            "cluster_id",
            "priority_band",
            "priority_score",
            "recommended_next_action",
            "cluster_confidence",
            "representative_name",
            "preferred_family_hint",
            "node_count",
            "root_row_count",
            "search_lead_count",
            "open_review_count",
            "receipt_count",
            "cluster_review_decision",
            "cluster_review_receipt_path",
            "cluster_review_parent_key",
            "max_source_object_score",
            "max_pair_evidence_score",
            "record_kind_counts",
            "inventory_status_counts",
            "review_decision_counts",
            "strict_keys",
            "review_keys",
            "manifest_paths",
            "example_node_names",
        ],
        args.replace,
    )
    write_tsv(PRIORITY_SUMMARY_TSV, summary_rows(clusters), ["metric", "value", "cluster_count"], args.replace)
    print(f"Clustered {len(nodes)} nodes into {len(clusters)} clusters.")


if __name__ == "__main__":
    main()
