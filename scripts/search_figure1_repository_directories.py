#!/usr/bin/env python3
"""Search repository directories for Figure 1 source surfaces.

This writes a searchsurface-* target, not a corporasearch-* manifest. Directory
records such as re3data repositories are places to search next, not themselves
Figure 1 corpora/databases.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree

import requests


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "steps/searches/figure1/searchsurface-repository-directory-re3data-replication-repositories.json"
CONTACT_EMAIL = os.environ.get("PROVENANCE_CONTACT_EMAIL", "rexdouglass@gmail.com").strip()
USER_AGENT = (
    "PublishedSmallNStudiesDontMatter figure1 repository-directory search "
    f"(mailto:{CONTACT_EMAIL}; noncommercial provenance research)"
)
TIMEOUT = (12, 30)
REQUEST_DELAY = float(os.environ.get("FIGURE1_SEARCH_DELAY_SECONDS", "0.35"))

QUERIES = [
    "replication",
    "reproduction archive",
    "replication archive",
    "social science data archive",
    "psychology data repository",
    "economics replication archive",
    "political science data archive",
    "clinical trial data repository",
    "open science framework",
]

FALSE_POSITIVE_TERMS = [
    "dna replication",
    "genome replication",
    "database replication",
    "replication fork",
    "viral replication",
]


def safe_text(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "").replace("\t", " ")).strip()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def child_text(node: ElementTree.Element, name: str) -> str:
    child = node.find(name)
    return safe_text(child.text if child is not None else "")


def search_re3data(query: str) -> tuple[list[dict[str, str]], list[str]]:
    rows: list[dict[str, str]] = []
    errors: list[str] = []
    try:
        response = requests.get(
            "https://www.re3data.org/api/beta/repositories",
            params={"query": query},
            headers={"User-Agent": USER_AGENT, "Accept": "application/xml"},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        root = ElementTree.fromstring(response.content)
        for repo in root.findall(".//repository"):
            repo_id = child_text(repo, "id")
            name = child_text(repo, "name")
            doi = child_text(repo, "doi")
            link = ""
            link_node = repo.find("link")
            if link_node is not None:
                link = safe_text(link_node.attrib.get("href", ""))
            joined = f"{name} {doi} {link}".lower()
            rows.append(
                {
                    "provider": "re3data",
                    "query": query,
                    "repository_id": repo_id,
                    "name": name,
                    "doi": doi,
                    "api_url": link,
                    "landing_url": f"https://www.re3data.org/repository/{repo_id}" if repo_id else "",
                    "surface_status": (
                        "possible_search_surface"
                        if not any(term in joined for term in FALSE_POSITIVE_TERMS)
                        else "likely_false_positive_surface"
                    ),
                    "next_action": "decide_whether_to_build_scoped_repository_adapter",
                }
            )
    except Exception as exc:
        errors.append(f"re3data::{query}::{type(exc).__name__}: {exc}")
    time.sleep(REQUEST_DELAY)
    return rows, errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replace", action="store_true", help="Replace existing target.")
    args = parser.parse_args()
    if OUT.exists() and not args.replace:
        print(f"Skipped {OUT.relative_to(ROOT)} because it already exists. Use --replace to rerun.")
        return

    rows: list[dict[str, str]] = []
    errors: list[str] = []
    for query in QUERIES:
        query_rows, query_errors = search_re3data(query)
        rows.extend(query_rows)
        errors.extend(query_errors)

    deduped: dict[str, dict[str, str]] = {}
    for row in rows:
        key = row.get("repository_id") or row.get("doi") or row.get("name", "").lower()
        if key and key not in deduped:
            deduped[key] = row

    OUT.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "manifest_id": OUT.stem,
        "strategy_id": "plot1_corpusdb_repository_directory_surface_search",
        "created_at": utc_now(),
        "user_agent": USER_AGENT,
        "raw_result_count": len(rows),
        "surface_count": len(deduped),
        "queries": QUERIES,
        "errors": errors,
        "surfaces": sorted(deduped.values(), key=lambda row: (row["surface_status"], row["name"].lower())),
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)} ({len(deduped)} surfaces from {len(rows)} raw results)")


if __name__ == "__main__":
    main()
