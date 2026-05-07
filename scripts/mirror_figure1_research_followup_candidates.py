#!/usr/bin/env python3
"""Mirror public URLs from the 2026-05-04 Figure 1 follow-up research batch."""

from __future__ import annotations

import hashlib
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW_ROOT = ROOT / "data/raw/replication_projects/lead_harvest/figure1_research_followup_20260504"
STATUS_ROOT = ROOT / "steps/source_inventory/figure1/research_followup_20260504"
STATUS_TSV = STATUS_ROOT / "mirror-status.tsv"
USER_AGENT = "PublishedSmallNStudiesDontMatter-source-mirror/0.1"


@dataclass(frozen=True)
class Target:
    key: str
    name: str
    url: str
    expected_role: str


TARGETS: tuple[Target, ...] = (
    Target("ying_bmj_ebm", "Ying/Ehrhardt pilot-to-full-scale efficacy", "https://doi.org/10.1136/bmjebm-2023-112358", "article_landing"),
    Target("ying_dissertation", "Ying JHU dissertation", "https://jscholarship.library.jhu.edu/items/02a9c0bb-56c1-41ab-9017-ff6793260f0b", "dissertation_landing"),
    Target("ying_jama_feasibility", "Ying/Ehrhardt JAMA feasibility", "https://jamanetwork.com/journals/jamanetworkopen/fullarticle/2809388", "article_landing"),
    Target("beets_childhood_rgb", "Childhood obesity RGB pilot-vs-larger trials", "https://doi.org/10.1186/s12966-020-0918-y", "article_landing"),
    Target("adult_obesity_rgb", "Adult obesity RGB pilot-vs-larger trials", "https://www.repository.cam.ac.uk/handle/1810/330818", "repository_landing"),
    Target("health_behavior_rgb_pubmed", "Health behavior RGB study", "https://pubmed.ncbi.nlm.nih.gov/38464006/", "article_metadata"),
    Target("health_behavior_rgb_researchsquare", "Health behavior RGB preprint", "https://doi.org/10.21203/rs.3.rs-3897976/v1", "preprint_landing"),
    Target("rct_duplicate", "RCT-DUPLICATE all trial results", "https://raw.githubusercontent.com/CharlotteMicheloud/RWE/main/data/all_trials_results.csv", "result_table"),
    Target("rct_duplicate", "RCT-DUPLICATE corrected trial results", "https://raw.githubusercontent.com/CharlotteMicheloud/RWE/main/data/all_trials_results_corrected.csv", "result_table"),
    Target("rct_duplicate", "RCT-DUPLICATE covariates", "https://raw.githubusercontent.com/CharlotteMicheloud/RWE/main/data/all_trials_covariates.csv", "covariate_table"),
    Target("rct_duplicate", "RCT-DUPLICATE margins", "https://raw.githubusercontent.com/CharlotteMicheloud/RWE/main/data/margins.csv", "context_table"),
    Target("forrt_reversals", "FORRT Replications and Reversals", "https://forrt.org/reversals/", "html_database"),
    Target("scaleup_physical_activity", "Physical activity scale-up review", "https://pmc.ncbi.nlm.nih.gov/articles/PMC7821550/", "article_landing"),
    Target("scaleup_nutrition", "Nutrition scale-up review", "https://doi.org/10.1093/nutrit/nuab096", "article_landing"),
)


def slug(value: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9]+", "_", value).strip("_").lower()
    return text[:80] or "download"


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except Exception:
        return str(path)


def fetch(target: Target, index: int) -> dict[str, str]:
    out_dir = RAW_ROOT / target.key
    out_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{index:02d}_{slug(target.expected_role)}_{slug(target.url)}.bin"
    out_path = out_dir / filename
    req = urllib.request.Request(target.url, headers={"User-Agent": USER_AGENT})
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            body = response.read()
            out_path.write_bytes(body)
            sha = hashlib.sha256(body).hexdigest()
            return {
                "candidate_key": target.key,
                "candidate_name": target.name,
                "url": target.url,
                "expected_role": target.expected_role,
                "status": "mirrored",
                "http_status": str(getattr(response, "status", "")),
                "final_url": response.url,
                "content_type": response.headers.get("content-type", ""),
                "content_length": str(len(body)),
                "local_path": rel(out_path),
                "sha256": sha,
                "attempted_at": started,
                "error": "",
            }
    except urllib.error.HTTPError as exc:
        return {
            "candidate_key": target.key,
            "candidate_name": target.name,
            "url": target.url,
            "expected_role": target.expected_role,
            "status": "blocked_http_error",
            "http_status": str(exc.code),
            "final_url": target.url,
            "content_type": exc.headers.get("content-type", "") if exc.headers else "",
            "content_length": "",
            "local_path": "",
            "sha256": "",
            "attempted_at": started,
            "error": str(exc),
        }
    except Exception as exc:
        return {
            "candidate_key": target.key,
            "candidate_name": target.name,
            "url": target.url,
            "expected_role": target.expected_role,
            "status": "blocked_error",
            "http_status": "",
            "final_url": target.url,
            "content_type": "",
            "content_length": "",
            "local_path": "",
            "sha256": "",
            "attempted_at": started,
            "error": f"{type(exc).__name__}: {exc}",
        }


def main() -> None:
    STATUS_ROOT.mkdir(parents=True, exist_ok=True)
    rows = [fetch(target, index) for index, target in enumerate(TARGETS, start=1)]
    columns = [
        "candidate_key",
        "candidate_name",
        "url",
        "expected_role",
        "status",
        "http_status",
        "final_url",
        "content_type",
        "content_length",
        "local_path",
        "sha256",
        "attempted_at",
        "error",
    ]
    with STATUS_TSV.open("w", encoding="utf-8") as handle:
        handle.write("\t".join(columns) + "\n")
        for row in rows:
            handle.write("\t".join(str(row.get(col, "")).replace("\t", " ").replace("\n", " ") for col in columns) + "\n")
    mirrored = sum(row["status"] == "mirrored" for row in rows)
    print(f"Wrote {STATUS_TSV}")
    print(f"Mirrored {mirrored}/{len(rows)} URLs")


if __name__ == "__main__":
    main()
