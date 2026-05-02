#!/usr/bin/env python3
"""Harvest special Figure 1 source-family surfaces.

These are bounded, named checks that generic scholarly/repository APIs do not
cover well: OpenReview challenge groups, static source-family pages, and known
project homepages from the coverage-audit seed list.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

import search_figure1_corpora_databases as search_core


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "steps/searches/figure1/corporasearch-specialsurfaces-expanded-openreview-rescience-gpt-source-family-pages.json"
CONTACT_EMAIL = os.environ.get("PROVENANCE_CONTACT_EMAIL", "rexdouglass@gmail.com").strip()
USER_AGENT = (
    "PublishedSmallNStudiesDontMatter figure1 special source-family search "
    f"(mailto:{CONTACT_EMAIL}; noncommercial provenance research)"
)
TIMEOUT = (12, 30)

OPENREVIEW_GROUP_PREFIXES = [
    "ML_Reproducibility_Challenge",
]

KNOWN_SOURCE_PAGES = [
    {
        "name": "FORRT large-scale replication projects hub",
        "url": "https://forrt.org/replication-hub/large-scale-replication-projects/",
        "query": "FORRT large-scale replication projects",
        "description": "Known source-family hub for large-scale replication projects and aliases that can seed Figure 1 corpus/database discovery.",
    },
    {
        "name": "Institute for Replication",
        "url": "https://i4replication.org/",
        "query": "Institute for Replication Replication Games",
        "description": "Known source-family page for social-science reproductions, robustness checks, Replication Games, and related outputs.",
    },
    {
        "name": "ReproSci Fly Immunity Workspace",
        "url": "https://reprosci.epfl.ch/",
        "query": "ReproSci Fly immunity claims articles comments",
        "description": "Known source-family workspace for Drosophila immunity claim reproducibility evidence.",
    },
    {
        "name": "REPEAT Initiative",
        "url": "https://www.repeatinitiative.org/",
        "query": "REPEAT Initiative healthcare database reproducibility",
        "description": "Known source-family project page for reproducibility and robustness of healthcare database research.",
    },
    {
        "name": "ReScience C contents",
        "url": "https://rescience.github.io/read/",
        "query": "ReScience C replication contents code DOI review URL",
        "description": "Static journal/source-family contents page for computational replication articles and code/review metadata.",
    },
    {
        "name": "X-Phi Replicability Project",
        "url": "https://experimental-philosophy.yale.edu/xphipage/Experimental%20Philosophy-Replications.html",
        "query": "Experimental Philosophy Replicability Project OSF data",
        "description": "Known source-family page listing experimental-philosophy replications by original paper.",
    },
    {
        "name": "Data Colada replication archive",
        "url": "https://datacolada.org/archives/category/replication",
        "query": "Data Replicada Data Colada replication archive",
        "description": "Known source-family/blog archive for consumer-psychology replication reports and related project links.",
    },
    {
        "name": "ManyBabies",
        "url": "https://manybabies.org/",
        "query": "ManyBabies replication OSF data",
        "description": "Known many-lab developmental psychology project family; requires explicit original-target gate before Figure 1 promotion.",
    },
    {
        "name": "ManyPrimates",
        "url": "https://manyprimates.github.io/",
        "query": "ManyPrimates replication OSF data",
        "description": "Known many-lab comparative cognition project family; likely manual/context unless explicit original-target pair evidence exists.",
    },
    {
        "name": "EGAP Metaketa Initiative",
        "url": "https://egap.org/our-work/the-metaketa-initiative/",
        "query": "EGAP Metaketa replication files coordinated trials",
        "description": "Known coordinated-trials source family that may expose replication files or component project repositories.",
    },
    {
        "name": "Sports Science Replication Centre",
        "url": "https://ssreplicationcentre.com/",
        "query": "Sports Science Replication Centre data",
        "description": "Known sports/exercise science replication source-family page.",
    },
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def safe_text(value: object, max_len: int = 1600) -> str:
    return re.sub(r"\s+", " ", str(value or "").replace("\t", " ")).strip()[:max_len]


def session() -> requests.Session:
    sess = requests.Session()
    sess.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json,text/html"})
    return sess


def text_title(html: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.I | re.S)
    return safe_text(re.sub(r"<[^>]+>", " ", match.group(1))) if match else ""


def html_summary(html: str) -> str:
    title = text_title(html)
    links = len(re.findall(r"<a\b", html, flags=re.I))
    return f"title={title}; html_bytes={len(html.encode('utf-8', errors='ignore'))}; link_count={links}"


def openreview_groups(sess: requests.Session) -> tuple[list[dict[str, str]], list[str]]:
    rows: list[dict[str, str]] = []
    errors: list[str] = []
    for prefix in OPENREVIEW_GROUP_PREFIXES:
        try:
            response = sess.get(
                "https://api2.openreview.net/groups",
                params={"prefix": prefix, "limit": 100},
                timeout=TIMEOUT,
            )
            response.raise_for_status()
            for group in response.json().get("groups", []):
                if not isinstance(group, dict):
                    continue
                group_id = safe_text(group.get("id", ""))
                if not group_id or group_id == prefix:
                    continue
                rows.append(
                    search_core.raw_result(
                        strategy="repository",
                        provider="openreview",
                        query=prefix,
                        title=group_id.replace("_", " "),
                        description=(
                            "OpenReview source-family/challenge group discovered by prefix lookup; "
                            f"parent={group.get('parent', '')}; host={group.get('host', '')}; "
                            "needs note/invitation inventory to enumerate reproducibility reports and original-paper links."
                        ),
                        landing_url=f"https://openreview.net/group?id={group_id}",
                        raw_url=response.url,
                        external_id=group_id,
                        extra={"parent": group.get("parent", ""), "host": group.get("host", "")},
                    )
                )
        except Exception as exc:
            errors.append(f"openreview::{prefix}::{type(exc).__name__}: {exc}")
    return rows, errors


def known_pages(sess: requests.Session) -> tuple[list[dict[str, str]], list[str]]:
    rows: list[dict[str, str]] = []
    errors: list[str] = []
    for page in KNOWN_SOURCE_PAGES:
        try:
            response = sess.get(page["url"], timeout=TIMEOUT)
            response.raise_for_status()
            summary = html_summary(response.text)
            rows.append(
                search_core.raw_result(
                    strategy="repository",
                    provider="known_source_page",
                    query=page["query"],
                    title=page["name"],
                    description=f"{page['description']} Page check: {summary}",
                    landing_url=page["url"],
                    raw_url=response.url,
                    external_id=page["url"],
                    extra={"http_status": response.status_code, "content_type": response.headers.get("content-type", "")},
                )
            )
        except Exception as exc:
            errors.append(f"known_source_page::{page['url']}::{type(exc).__name__}: {exc}")
    return rows, errors


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replace", action="store_true", help="Replace existing target.")
    args = parser.parse_args()
    if OUT.exists() and not args.replace:
        print(f"Skipped {OUT.relative_to(ROOT)} because it already exists. Use --replace to rerun.")
        return

    sess = session()
    raw_rows: list[dict[str, str]] = []
    errors: list[str] = []
    for rows, errs in [openreview_groups(sess), known_pages(sess)]:
        raw_rows.extend(rows)
        errors.extend(errs)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    search_core.write_manifest(
        OUT,
        strategy_id="plot1_corpusdb_special_source_surface_search",
        strategy="repository",
        providers=["openreview", "known_source_page"],
        queries=OPENREVIEW_GROUP_PREFIXES + [page["query"] for page in KNOWN_SOURCE_PAGES],
        raw_rows=raw_rows,
        errors=errors,
        replace=True,
    )


if __name__ == "__main__":
    main()
