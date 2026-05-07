#!/usr/bin/env python3
"""Mirror the 2026-05-04 GPT-suggested Figure 1 corpus candidates.

This is intentionally small and manifest-driven. Large mirrored bytes are
written under data/raw/replication_projects/lead_harvest/ and ignored by git.
Compact status/provenance ledgers are written under steps/source_inventory.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html.parser
import json
import mimetypes
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW_ROOT = REPO_ROOT / "data/raw/replication_projects/lead_harvest/gpt_many_replication_candidates_20260504"
DEFAULT_STATUS_ROOT = REPO_ROOT / "steps/source_inventory/figure1/gpt_many_replication_candidates_20260504"

USER_AGENT = "PublishedSmallNStudiesDontMatter-source-mirror/0.1 (+https://github.com/)"
MAX_DOWNLOAD_BYTES = 150 * 1024 * 1024


@dataclass(frozen=True)
class Candidate:
    key: str
    name: str
    priority: str
    initial_decision: str
    current_repo_status: str
    urls: tuple[str, ...]
    notes: str = ""
    osf_nodes: tuple[str, ...] = ()
    zenodo_records: tuple[str, ...] = ()
    github_archives: tuple[str, ...] = ()


CANDIDATES: tuple[Candidate, ...] = (
    Candidate(
        key="eprp_xphi",
        name="Experimental Philosophy Replicability Project / X-Phi",
        priority="known_covered_check",
        initial_decision="duplicate_or_support",
        current_repo_status="already_integrated_live_rows",
        urls=(
            "https://osf.io/dvkpr/",
            "https://osf.io/4ewkh/download",
            "https://cran.r-project.org/package=ReplicationSuccess",
        ),
        osf_nodes=("dvkpr",),
        notes="Current root table already has EPRP rows from XPhiReplicability_CompleteData.csv.",
    ),
    Candidate(
        key="management_science_replication_project",
        name="Management Science Replication Project",
        priority="known_covered_check",
        initial_decision="duplicate_or_support",
        current_repo_status="already_integrated_live_rows",
        urls=(
            "https://msreplication.utdallas.edu/",
            "https://msreplication.utdallas.edu/replication-principles/",
            "https://msreplication.utdallas.edu/chen-et-al-2013/",
            "https://msreplication.utdallas.edu/files/2026/02/CrosonDonohue2006_DataAnalysisStimuli.zip",
            "https://msreplication.utdallas.edu/files/2026/02/ShunkoEtAl2018_DataAnalysisStimuli.zip",
        ),
        notes="Current root table already has MSRP report-table rows; mirror pass may find newer zips.",
    ),
    Candidate(
        key="brazilian_reproducibility_initiative",
        name="Brazilian Reproducibility Initiative",
        priority="known_covered_check",
        initial_decision="duplicate_or_support",
        current_repo_status="already_integrated_live_rows",
        urls=(
            "https://github.com/BrazilianReproducibilityInitiative/bri-analysis",
            "https://github.com/BrazilianReproducibilityInitiative/bri-analysis/archive/refs/heads/main.zip",
            "https://osf.io/6av7k/wiki",
        ),
        github_archives=("https://github.com/BrazilianReproducibilityInitiative/bri-analysis/archive/refs/heads/main.zip",),
        osf_nodes=("6av7k",),
        notes="Current root table already has BRI primary-analysis experiment rows.",
    ),
    Candidate(
        key="sports_science_replication_centre",
        name="Sports Science Replication Centre",
        priority="known_covered_check",
        initial_decision="duplicate_or_support",
        current_repo_status="already_integrated_live_rows",
        urls=(
            "https://ssreplicationcentre.com/",
            "https://ssreplicationcentre.com/replications/",
            "https://ssreplicationcentre.com/publication/estimating_replicability/",
            "https://osf.io/3vufg/",
        ),
        osf_nodes=("3vufg",),
        notes="Current root table already has sports supplemental outcome rows.",
    ),
    Candidate(
        key="hagen_hcsp",
        name="Hagen Cumulative Science Project I",
        priority="mirror_first_net_new",
        initial_decision="maybe_pass_after_custom_parser",
        current_repo_status="not_integrated_access_route_checked",
        urls=(
            "https://osf.io/d7za8/",
            "https://github.com/pandorica-opens/Hagen-Cumulative-Science-Project-I",
            "https://github.com/pandorica-opens/Hagen-Cumulative-Science-Project-I/archive/refs/heads/master.zip",
            "https://docs.google.com/spreadsheets/d/1VBnEGbanAt5yLXkpMGRGJWZeuw1TLNVudksgXyksHq0/edit?ts=5beae9fc#gid=0",
            "https://docs.google.com/spreadsheets/d/1f5QYC1F-Pd2v9N4DU6Yf29jdKPhOzdad6B2GDhWoVjM/edit?usp=sharing",
        ),
        github_archives=("https://github.com/pandorica-opens/Hagen-Cumulative-Science-Project-I/archive/refs/heads/master.zip",),
        osf_nodes=("d7za8",),
        notes="GitHub Shiny app is mirrorable; its backing Google Sheets currently return file-deleted/410 in this environment.",
    ),
    Candidate(
        key="many_smiles",
        name="Many Smiles Collaboration",
        priority="mirror_first_net_new",
        initial_decision="maybe_pass_after_custom_parser",
        current_repo_status="mirrored_context_not_integrated",
        urls=(
            "https://manysmilescollaboration.com/",
            "https://www.nature.com/articles/s41562-022-01458-9",
            "https://osf.io/download/qd2s3/",
        ),
        notes="OSF data zip is mirrorable, but original benchmark effect/N is not a clean row table in the mirrored zip.",
    ),
    Candidate(
        key="asset_market_replications",
        name="High-powered preregistered replications of experimental asset-market results",
        priority="mirror_first_net_new",
        initial_decision="maybe_pass_after_custom_parser",
        current_repo_status="not_integrated_seen_as_net_new",
        urls=(
            "https://doi.org/10.2139/ssrn.5048949",
            "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5048949",
            "https://osf.io/uxrgk/",
            "https://osf.io/aepxt/",
        ),
        osf_nodes=("uxrgk", "aepxt"),
    ),
    Candidate(
        key="sensory_marketing_replications",
        name="Replications of ten influential sensory-marketing studies",
        priority="mirror_first_net_new",
        initial_decision="maybe_pass_after_custom_parser",
        current_repo_status="not_integrated_seen_as_net_new",
        urls=(
            "https://osf.io/tnmvq/",
            "https://doi.org/10.1016/j.jbusres.2022.05.006",
            "https://www.frontiersin.org/journals/communication/articles/10.3389/fcomm.2022.1048896/full",
        ),
        osf_nodes=("tnmvq",),
    ),
    Candidate(
        key="transparent_replications_clearer_thinking",
        name="Transparent Replications by Clearer Thinking",
        priority="mirror_first_net_new",
        initial_decision="maybe_pass_after_custom_parser",
        current_repo_status="not_integrated_seen_as_net_new",
        urls=(
            "https://doi.org/10.5281/zenodo.17705056",
            "https://doi.org/10.5281/zenodo.17705407",
            "https://doi.org/10.5281/zenodo.17705573",
        ),
        zenodo_records=("17705056", "17705407", "17705573"),
    ),
    Candidate(
        key="replicability_project_health_behavior",
        name="Replicability Project: Health Behavior",
        priority="context_check",
        initial_decision="context_only_pending_final_results",
        current_repo_status="not_integrated_context",
        urls=(
            "https://www.cos.io/rphb",
            "https://www.cos.io/initiatives/replicability-project-health-behavior",
            "https://osf.io/pxmj9/",
        ),
        osf_nodes=("pxmj9",),
    ),
    Candidate(
        key="repeat_initiative",
        name="REPEAT Initiative",
        priority="mirror_first_net_new",
        initial_decision="promoted_after_custom_parser_method_labeled",
        current_repo_status="promoted_live_rows_batch2",
        urls=(
            "https://repeatinitiative.org/",
            "https://osf.io/my5gn/",
            "https://doi.org/10.17605/OSF.IO/MY5GN",
            "https://www.nature.com/articles/s41467-022-32310-3",
        ),
        osf_nodes=("my5gn",),
        notes="Batch-two mining promotes 106 primary ratio-measure rows, with same-data RWE reproduction explicitly labeled.",
    ),
    Candidate(
        key="fred_replication_database",
        name="FReD / The Replication Database",
        priority="duplicate_support",
        initial_decision="duplicate_or_support",
        current_repo_status="already_known_dedupe_support",
        urls=(
            "https://forrt.org/replication-database/",
            "https://osf.io/9r62x/",
            "https://osf.io/z5u9b/download",
            "https://osf.io/qtkzy/",
            "https://osf.io/c9rny/",
        ),
        osf_nodes=("9r62x", "qtkzy", "c9rny"),
    ),
    Candidate(
        key="crep",
        name="Collaborative Replications and Education Project / CREP",
        priority="context_check",
        initial_decision="context_only_needs_aggregate_export",
        current_repo_status="not_integrated_context",
        urls=("https://osf.io/wfc6u/",),
        osf_nodes=("wfc6u",),
    ),
    Candidate(
        key="threeie_replication_paper_series",
        name="3ie Replication Paper Series",
        priority="false_positive_support",
        initial_decision="context_only_internal_replication",
        current_repo_status="not_integrated_context",
        urls=("https://www.3ieimpact.org/evidence-hub/publications/replication-paper-series",),
    ),
    Candidate(
        key="i4r_replication_games",
        name="Institute for Replication / I4R / Replication Games",
        priority="false_positive_support",
        initial_decision="context_only_same_data_reproduction",
        current_repo_status="not_integrated_context",
        urls=("https://i4replication.org/", "https://i4replication.org/meta-database/", "https://i4replication.org/reports/"),
    ),
    Candidate(
        key="replicationwiki",
        name="ReplicationWiki",
        priority="false_positive_support",
        initial_decision="likely_fail_no_dn_fields",
        current_repo_status="not_integrated_context",
        urls=("https://replication.uni-goettingen.de/wiki/",),
    ),
    Candidate(
        key="ml_reproducibility_challenge",
        name="ML Reproducibility Challenge",
        priority="false_positive_support",
        initial_decision="context_only_metric_mismatch",
        current_repo_status="not_integrated_context",
        urls=("https://openreview.net/group?id=ML_Reproducibility_Challenge/2022", "https://paperswithcode.com/rc2022"),
    ),
    Candidate(
        key="rescience_c",
        name="ReScience C",
        priority="false_positive_support",
        initial_decision="likely_fail_metric_mismatch",
        current_repo_status="not_integrated_context",
        urls=("https://rescience.github.io/", "https://github.com/ReScience"),
    ),
)


class LinkParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        attrs_dict = dict(attrs)
        href = attrs_dict.get("href")
        if href:
            self.links.append(href)


def safe_filename(url: str, content_type: str | None = None) -> str:
    parsed = urllib.parse.urlparse(url)
    name = Path(parsed.path).name or parsed.netloc or "landing"
    if not Path(name).suffix and content_type:
        guessed = mimetypes.guess_extension(content_type.split(";")[0].strip())
        if guessed:
            name += guessed
    if not Path(name).suffix:
        name += ".html"
    clean = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("_")
    if len(clean) > 120:
        stem = Path(clean).stem[:90]
        suffix = Path(clean).suffix
        clean = stem + suffix
    return clean or "download.bin"


def unique_filename(url: str, content_type: str | None = None) -> str:
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]
    return f"{digest}__{safe_filename(url, content_type)}"


def sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def request_url(url: str, timeout: int = 30) -> urllib.request.Request:
    return urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})


def fetch_url(url: str, out_dir: Path, replace: bool) -> dict[str, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    started = time.time()
    row: dict[str, str] = {
        "url": url,
        "status": "started",
        "http_status": "",
        "content_type": "",
        "local_path": "",
        "sha256": "",
        "size_bytes": "",
        "elapsed_sec": "",
        "error": "",
    }
    try:
        with urllib.request.urlopen(request_url(url), timeout=30) as resp:
            status = getattr(resp, "status", "")
            content_type = resp.headers.get("Content-Type", "")
            length = resp.headers.get("Content-Length")
            if length and int(length) > MAX_DOWNLOAD_BYTES:
                row.update(
                    {
                        "status": "skipped_too_large",
                        "http_status": str(status),
                        "content_type": content_type,
                        "size_bytes": length,
                    }
                )
                return row
            filename = unique_filename(url, content_type)
            out_path = out_dir / filename
            if out_path.exists() and not replace:
                row.update(
                    {
                        "status": "already_local",
                        "http_status": str(status),
                        "content_type": content_type,
                        "local_path": str(out_path.relative_to(REPO_ROOT)),
                        "sha256": sha256_path(out_path),
                        "size_bytes": str(out_path.stat().st_size),
                    }
                )
                return row
            tmp_path = out_path.with_suffix(out_path.suffix + ".tmp")
            total = 0
            with tmp_path.open("wb") as f:
                while True:
                    chunk = resp.read(1024 * 1024)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > MAX_DOWNLOAD_BYTES:
                        tmp_path.unlink(missing_ok=True)
                        row.update(
                            {
                                "status": "skipped_too_large_stream",
                                "http_status": str(status),
                                "content_type": content_type,
                                "size_bytes": str(total),
                            }
                        )
                        return row
                    f.write(chunk)
            tmp_path.replace(out_path)
            row.update(
                {
                    "status": "downloaded",
                    "http_status": str(status),
                    "content_type": content_type,
                    "local_path": str(out_path.relative_to(REPO_ROOT)),
                    "sha256": sha256_path(out_path),
                    "size_bytes": str(out_path.stat().st_size),
                }
            )
            return row
    except urllib.error.HTTPError as exc:
        row.update({"status": "http_error", "http_status": str(exc.code), "error": str(exc)})
        return row
    except Exception as exc:  # noqa: BLE001
        row.update({"status": "failed", "error": repr(exc)})
        return row
    finally:
        row["elapsed_sec"] = f"{time.time() - started:.2f}"


def read_text_if_html(row: dict[str, str]) -> str:
    path = row.get("local_path")
    ctype = row.get("content_type", "")
    if not path or ("html" not in ctype and not path.endswith((".html", ".htm"))):
        return ""
    full = REPO_ROOT / path
    try:
        return full.read_text(errors="ignore")
    except Exception:
        return ""


def discover_html_links(row: dict[str, str]) -> list[str]:
    text = read_text_if_html(row)
    if not text:
        return []
    parser = LinkParser()
    parser.feed(text)
    base = row["url"]
    out: list[str] = []
    for link in parser.links:
        full = urllib.parse.urldefrag(urllib.parse.urljoin(base, link))[0]
        parsed = urllib.parse.urlparse(full)
        lower = full.lower()
        if "msreplication.utdallas.edu" in parsed.netloc and (
            lower.endswith(".zip")
            or lower.endswith(".pdf")
            or "dataanalysisstimuli" in lower
            or "replicationreport" in lower
        ):
            out.append(full)
        elif "clearerthinking" in parsed.netloc and ("replication" in lower or lower.endswith(".pdf")):
            out.append(full)
    return sorted(set(out))


def osf_api_url(node: str) -> str:
    return f"https://api.osf.io/v2/nodes/{node}/files/osfstorage/"


def discover_osf_downloads(node: str, status_dir: Path, replace: bool) -> tuple[list[str], list[dict[str, str]]]:
    queue = deque([osf_api_url(node)])
    seen: set[str] = set()
    downloads: list[str] = []
    metadata_rows: list[dict[str, str]] = []
    metadata_dir = status_dir / "provider_metadata"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    idx = 0
    while queue:
        api_url = queue.popleft()
        if api_url in seen:
            continue
        seen.add(api_url)
        idx += 1
        meta_path = metadata_dir / f"osf_{node}_{idx:03d}.json"
        row = fetch_url(api_url, metadata_dir, replace=replace)
        row["provider"] = "osf"
        row["provider_id"] = node
        metadata_rows.append(row)
        local_path = row.get("local_path")
        if row.get("status") not in {"downloaded", "already_local"} or not local_path:
            continue
        fetched_path = REPO_ROOT / local_path
        if fetched_path != meta_path and fetched_path.exists():
            # Keep a stable, predictable metadata filename in addition to the URL-derived name.
            if replace or not meta_path.exists():
                meta_path.write_bytes(fetched_path.read_bytes())
        try:
            data = json.loads(fetched_path.read_text())
        except Exception:
            continue
        for item in data.get("data", []):
            links = item.get("links") or {}
            attrs = item.get("attributes") or {}
            kind = attrs.get("kind") or item.get("type")
            if kind == "file" and links.get("download"):
                downloads.append(links["download"])
            rel_files = (((item.get("relationships") or {}).get("files") or {}).get("links") or {}).get("related", {})
            related_href = rel_files.get("href") if isinstance(rel_files, dict) else None
            if kind == "folder" and related_href:
                queue.append(related_href)
        next_url = ((data.get("links") or {}).get("next"))
        if next_url:
            queue.append(next_url)
    return sorted(set(downloads)), metadata_rows


def discover_zenodo_downloads(record: str, status_dir: Path, replace: bool) -> tuple[list[str], list[dict[str, str]]]:
    api_url = f"https://zenodo.org/api/records/{record}"
    metadata_dir = status_dir / "provider_metadata"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    row = fetch_url(api_url, metadata_dir, replace=replace)
    row["provider"] = "zenodo"
    row["provider_id"] = record
    downloads: list[str] = []
    local_path = row.get("local_path")
    if row.get("status") in {"downloaded", "already_local"} and local_path:
        try:
            data = json.loads((REPO_ROOT / local_path).read_text())
            for item in data.get("files", []):
                links = item.get("links") or {}
                url = links.get("self") or links.get("download")
                if url:
                    downloads.append(url)
        except Exception as exc:  # noqa: BLE001
            row["error"] = f"{row.get('error', '')}; parse_error={exc!r}".strip("; ")
    return sorted(set(downloads)), [row]


def manifest_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for cand in CANDIDATES:
        rows.append(
            {
                "candidate_key": cand.key,
                "candidate_name": cand.name,
                "priority": cand.priority,
                "initial_decision": cand.initial_decision,
                "current_repo_status": cand.current_repo_status,
                "seed_urls": " | ".join(cand.urls),
                "osf_nodes": " | ".join(cand.osf_nodes),
                "zenodo_records": " | ".join(cand.zenodo_records),
                "github_archives": " | ".join(cand.github_archives),
                "notes": cand.notes,
            }
        )
    return rows


def write_tsv(path: Path, rows: Iterable[dict[str, str]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-root", type=Path, default=DEFAULT_RAW_ROOT)
    parser.add_argument("--status-root", type=Path, default=DEFAULT_STATUS_ROOT)
    parser.add_argument("--replace", action="store_true")
    parser.add_argument(
        "--include-priorities",
        default="mirror_first_net_new,known_covered_check,context_check,methodology_review,duplicate_support,false_positive_support",
        help="Comma-separated priority labels to mirror. Manifest is always written.",
    )
    args = parser.parse_args(argv)

    raw_root = args.raw_root
    status_root = args.status_root
    raw_root.mkdir(parents=True, exist_ok=True)
    status_root.mkdir(parents=True, exist_ok=True)
    include = {x.strip() for x in args.include_priorities.split(",") if x.strip()}

    manifest = manifest_rows()
    write_tsv(
        status_root / "candidate-intake-ledger.tsv",
        manifest,
        [
            "candidate_key",
            "candidate_name",
            "priority",
            "initial_decision",
            "current_repo_status",
            "seed_urls",
            "osf_nodes",
            "zenodo_records",
            "github_archives",
            "notes",
        ],
    )

    status_rows: list[dict[str, str]] = []
    metadata_rows: list[dict[str, str]] = []
    discovered_rows: list[dict[str, str]] = []

    for cand in CANDIDATES:
        if cand.priority not in include:
            continue
        cand_dir = raw_root / cand.key
        candidate_urls: set[str] = set(cand.urls) | set(cand.github_archives)

        for node in cand.osf_nodes:
            downloads, meta = discover_osf_downloads(node, status_root, args.replace)
            metadata_rows.extend(dict(m, candidate_key=cand.key, candidate_name=cand.name) for m in meta)
            for url in downloads:
                discovered_rows.append(
                    {
                        "candidate_key": cand.key,
                        "candidate_name": cand.name,
                        "provider": "osf",
                        "provider_id": node,
                        "url": url,
                    }
                )
            candidate_urls.update(downloads)

        for record in cand.zenodo_records:
            downloads, meta = discover_zenodo_downloads(record, status_root, args.replace)
            metadata_rows.extend(dict(m, candidate_key=cand.key, candidate_name=cand.name) for m in meta)
            for url in downloads:
                discovered_rows.append(
                    {
                        "candidate_key": cand.key,
                        "candidate_name": cand.name,
                        "provider": "zenodo",
                        "provider_id": record,
                        "url": url,
                    }
                )
            candidate_urls.update(downloads)

        queue = deque(sorted(candidate_urls))
        seen: set[str] = set()
        while queue:
            url = queue.popleft()
            if url in seen:
                continue
            seen.add(url)
            row = fetch_url(url, cand_dir, args.replace)
            row.update(
                {
                    "candidate_key": cand.key,
                    "candidate_name": cand.name,
                    "priority": cand.priority,
                    "initial_decision": cand.initial_decision,
                    "current_repo_status": cand.current_repo_status,
                }
            )
            status_rows.append(row)
            for discovered in discover_html_links(row):
                if discovered not in seen:
                    discovered_rows.append(
                        {
                            "candidate_key": cand.key,
                            "candidate_name": cand.name,
                            "provider": "html_link",
                            "provider_id": url,
                            "url": discovered,
                        }
                    )
                    queue.append(discovered)

    write_tsv(
        status_root / "mirror-status.tsv",
        status_rows,
        [
            "candidate_key",
            "candidate_name",
            "priority",
            "initial_decision",
            "current_repo_status",
            "url",
            "status",
            "http_status",
            "content_type",
            "local_path",
            "sha256",
            "size_bytes",
            "elapsed_sec",
            "error",
        ],
    )
    write_tsv(
        status_root / "provider-metadata-status.tsv",
        metadata_rows,
        [
            "candidate_key",
            "candidate_name",
            "provider",
            "provider_id",
            "url",
            "status",
            "http_status",
            "content_type",
            "local_path",
            "sha256",
            "size_bytes",
            "elapsed_sec",
            "error",
        ],
    )
    write_tsv(
        status_root / "discovered-download-urls.tsv",
        discovered_rows,
        ["candidate_key", "candidate_name", "provider", "provider_id", "url"],
    )
    print(f"wrote {len(status_rows)} mirror status rows to {status_root / 'mirror-status.tsv'}")
    print(f"wrote {len(metadata_rows)} provider metadata rows")
    print(f"wrote {len(discovered_rows)} discovered URL rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
