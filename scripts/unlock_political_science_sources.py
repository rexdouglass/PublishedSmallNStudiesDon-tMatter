#!/usr/bin/env python3
"""Probe and stage political-science/development preregistration rescue leads.

The goal is not to force these leads into strict Plot 3.  This script turns the
research notes into auditable artifacts:

- a compact AEA Registry governance queue,
- a package/API access manifest,
- native metric seed rows where the estimate is already visible, and
- a user TODO list for rows that still require manual selector/extraction work.
"""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import pandas as pd
import requests


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw" / "corpus_candidates" / "political_science_unlock"
DERIVED_DIR = ROOT / "data" / "derived" / "effect_inflation_dataset"
WORKLIST = DERIVED_DIR / "plot3_political_science_rescue_worklist.csv"

AEA_TRIALS_CSV = RAW_DIR / "aea_trials.csv"
AEA_METADATA_JSON = RAW_DIR / "aea_dataverse_metadata.json"

AEA_GOVERNANCE_OUT = DERIVED_DIR / "plot3_aea_registry_governance_candidates.csv"
PACKAGE_MANIFEST_OUT = DERIVED_DIR / "plot3_political_science_package_manifest.csv"
UNLOCK_STATUS_OUT = DERIVED_DIR / "plot3_political_science_unlock_status.csv"
NATIVE_SEEDS_OUT = DERIVED_DIR / "plot3_political_science_native_metric_seed_rows.csv"
TODO_OUT = DERIVED_DIR / "plot3_political_science_user_todos.csv"
MOUSA_D_CANDIDATES_OUT = DERIVED_DIR / "plot3_mousa2020_soccer_d_candidates.csv"

USER_AGENT = "Mozilla/5.0 PublishedSmallNStudiesPoliticalScienceUnlock/1.0"
TIMEOUT = (20, 60)

AEA_DATASET_API = "https://dataverse.harvard.edu/api/datasets/:persistentId/?persistentId=doi:10.7910/DVN/OHBI3I"
AEA_GUESTBOOK_RESPONSE = {
    "guestbookResponse": {
        "name": "Codex automated source audit",
        "email": "noreply@example.com",
        "institution": "OpenAI",
        "position": "Research assistant",
        "answers": [
            {"id": 241, "value": "Non-academic researcher"},
            {"id": 243, "value": "Meta-analysis/systematic review"},
            {
                "id": 242,
                "value": "Auditing public preregistration metadata for a D-vs-N evidence map.",
            },
            {"id": 240, "value": "No"},
        ],
    }
}

GOVERNANCE_RE = re.compile(
    r"election|electoral|voter|vote|politic|governance|tax|police|"
    r"corruption|accountability|public service|public goods|democracy|"
    r"campaign|turnout|candidate|clientel|bureaucr|state capacity|"
    r"public finance|compliance|local government|transparency",
    flags=re.I,
)


def session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT})
    return s


def text_present(value: object) -> bool:
    if pd.isna(value):
        return False
    return bool(str(value).strip()) and str(value).strip().lower() != "nan"


def metadata_title(payload: dict[str, Any]) -> str:
    fields = (
        payload.get("data", {})
        .get("latestVersion", {})
        .get("metadataBlocks", {})
        .get("citation", {})
        .get("fields", [])
    )
    for field in fields:
        if field.get("typeName") == "title":
            return str(field.get("value", ""))
    return ""


def dataverse_dataset_api_for_doi(doi: str) -> str:
    return f"https://dataverse.harvard.edu/api/datasets/:persistentId/?persistentId=doi:{doi}"


def dataverse_doi_from_url(url: str) -> str | None:
    if not url:
        return None
    if "doi.org/10.7910/DVN/" in url:
        return url.split("doi.org/", 1)[1].strip().rstrip("/")
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    pid = qs.get("persistentId") or qs.get("persistentid")
    if pid:
        value = pid[0].replace("%3A", ":")
        if value.startswith("doi:"):
            return value[4:]
    return None


def fetch_json(s: requests.Session, url: str) -> tuple[dict[str, Any] | None, str]:
    try:
        r = s.get(url, timeout=TIMEOUT)
        if not r.ok:
            return None, f"http_{r.status_code}"
        return r.json(), "ok"
    except Exception as exc:  # noqa: BLE001 - manifest should preserve probe error text
        return None, f"{type(exc).__name__}: {exc}"


def ensure_aea_snapshot(s: requests.Session) -> dict[str, Any]:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    payload, status = fetch_json(s, AEA_DATASET_API)
    if payload is None:
        raise RuntimeError(f"AEA Dataverse metadata probe failed: {status}")
    AEA_METADATA_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    files = payload["data"]["latestVersion"]["files"]
    trials = next(f for f in files if f["dataFile"]["filename"] == "trials.csv")
    file_id = trials["dataFile"]["id"]
    if not AEA_TRIALS_CSV.exists() or AEA_TRIALS_CSV.stat().st_size < 1_000_000:
        ticket = s.post(
            f"https://dataverse.harvard.edu/api/access/datafile/{file_id}?signed=true",
            json=AEA_GUESTBOOK_RESPONSE,
            timeout=TIMEOUT,
        )
        ticket.raise_for_status()
        signed_url = ticket.json()["data"]["signedUrl"]
        tmp = AEA_TRIALS_CSV.with_suffix(".csv.part")
        with s.get(signed_url, stream=True, timeout=(30, 240)) as download:
            download.raise_for_status()
            with tmp.open("wb") as out:
                for chunk in download.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        out.write(chunk)
        tmp.rename(AEA_TRIALS_CSV)
    return payload


def build_aea_governance_queue() -> pd.DataFrame:
    df = pd.read_csv(AEA_TRIALS_CSV, low_memory=False)
    link_ready = (
        df["Analysis Plan Documents"].map(text_present)
        & df["Relevant papers for csv"].map(text_present)
        & (df["Public data url"].map(text_present) | df["Program files url"].map(text_present))
    )
    text_cols = [
        "Title",
        "Keywords",
        "Abstract",
        "Primary outcome end points",
        "Intervention",
        "Jel code",
    ]
    text = df[text_cols].fillna("").agg(" ".join, axis=1)
    governance = text.str.contains(GOVERNANCE_RE, regex=True)
    out = df.loc[link_ready & governance].copy()
    out["candidate_status"] = "aea_pap_paper_package_governance_candidate"
    out["row_rescue_recommendation"] = "stage_native_metric_first"
    out["strict_blocker"] = (
        "Registry supplies PAP/paper/package links and N fields, but final effect estimates "
        "must be extracted from the linked paper or replication package."
    )
    keep = [
        "RCT_ID",
        "Title",
        "Url",
        "Status",
        "First registered on",
        "Analysis Plan Documents",
        "Country names",
        "Keywords",
        "Primary outcome end points",
        "Sample size number clusters",
        "Sample size number observations",
        "Number of clusters",
        "Total number of observations",
        "Relevant papers for csv",
        "Public data url",
        "Program files url",
        "candidate_status",
        "row_rescue_recommendation",
        "strict_blocker",
    ]
    return out[keep].sort_values(["RCT_ID", "Title"]).reset_index(drop=True)


def iter_osf_files(s: requests.Session, node: str, provider: str = "osfstorage") -> list[dict[str, Any]]:
    root = f"https://api.osf.io/v2/nodes/{node}/files/{provider}/?page%5Bsize%5D=100"
    seen: set[str] = set()
    rows: list[dict[str, Any]] = []

    def walk(url: str, prefix: str = "") -> None:
        while url:
            payload, status = fetch_json(s, url)
            if payload is None:
                rows.append(
                    {
                        "kind": "probe_error",
                        "path": prefix,
                        "name": "",
                        "size": "",
                        "download_url": "",
                        "probe_status": status,
                    }
                )
                return
            for item in payload.get("data", []):
                item_id = item.get("id", "")
                if item_id in seen:
                    continue
                seen.add(item_id)
                attrs = item.get("attributes", {})
                links = item.get("links", {})
                name = attrs.get("name", "")
                kind = attrs.get("kind", "")
                path = f"{prefix}/{name}".strip("/")
                rows.append(
                    {
                        "kind": kind,
                        "path": path,
                        "name": name,
                        "size": attrs.get("size", ""),
                        "download_url": links.get("download", ""),
                        "probe_status": "ok",
                    }
                )
                if kind == "folder":
                    nested = (
                        item.get("relationships", {})
                        .get("files", {})
                        .get("links", {})
                        .get("related", {})
                        .get("href")
                    )
                    if nested:
                        walk(nested, path)
            url = payload.get("links", {}).get("next")

    walk(root)
    return rows


def probe_dataverse_package(s: requests.Session, url: str) -> list[dict[str, Any]]:
    doi = dataverse_doi_from_url(url)
    if not doi:
        return []
    payload, status = fetch_json(s, dataverse_dataset_api_for_doi(doi))
    if payload is None:
        return [
            {
                "artifact_type": "dataverse_dataset",
                "artifact_id": doi,
                "artifact_title": "",
                "file_count": "",
                "file_names_preview": "",
                "probe_status": status,
            }
        ]
    files = payload.get("data", {}).get("latestVersion", {}).get("files", [])
    names = [f.get("dataFile", {}).get("filename", "") for f in files]
    return [
        {
            "artifact_type": "dataverse_dataset",
            "artifact_id": doi,
            "artifact_title": metadata_title(payload),
            "file_count": len(files),
            "file_names_preview": "; ".join(names[:12]),
            "probe_status": "metadata_ok",
        }
    ]


def probe_osf_package(s: requests.Session, url: str) -> list[dict[str, Any]]:
    match = re.search(r"osf\.io/([a-z0-9]{5})", url, flags=re.I)
    if not match:
        return []
    node = match.group(1).lower()
    providers_payload, provider_status = fetch_json(s, f"https://api.osf.io/v2/nodes/{node}/files/")
    providers: list[str] = ["osfstorage"]
    if providers_payload is not None:
        providers = [
            item.get("attributes", {}).get("provider")
            for item in providers_payload.get("data", [])
            if item.get("attributes", {}).get("provider")
        ] or providers
    rows = []
    for provider in providers:
        files = iter_osf_files(s, node, provider)
        file_rows = [f for f in files if f.get("kind") == "file"]
        folder_rows = [f for f in files if f.get("kind") == "folder"]
        error_rows = [f for f in files if f.get("kind") == "probe_error"]
        rows.append(
            {
                "artifact_type": "osf_node",
                "artifact_id": f"{node}:{provider}",
                "artifact_title": "",
                "file_count": len(file_rows),
                "folder_count": len(folder_rows),
                "file_names_preview": "; ".join([f["path"] for f in file_rows[:12]]),
                "probe_status": error_rows[0]["probe_status"]
                if error_rows and not file_rows and not folder_rows
                else f"metadata_ok_provider_status_{provider_status}",
            }
        )
    return rows


def probe_zenodo(s: requests.Session, url: str) -> list[dict[str, Any]]:
    match = re.search(r"zenodo\.(?:org/records|org/record|org/doi/10\.5281/zenodo)\.?/?([0-9]+)", url)
    if not match:
        match = re.search(r"10\.5281/zenodo\.([0-9]+)", url)
    if not match:
        return []
    rec = match.group(1)
    payload, status = fetch_json(s, f"https://zenodo.org/api/records/{rec}")
    if payload is None:
        return [
            {
                "artifact_type": "zenodo_record",
                "artifact_id": rec,
                "artifact_title": "",
                "file_count": "",
                "file_names_preview": "",
                "probe_status": status,
            }
        ]
    return [
        {
            "artifact_type": "zenodo_record",
            "artifact_id": rec,
            "artifact_title": payload.get("metadata", {}).get("title", ""),
            "file_count": len(payload.get("files", [])),
            "file_names_preview": "; ".join(f.get("key", "") for f in payload.get("files", [])[:12]),
            "probe_status": "metadata_ok",
        }
    ]


def probe_github(s: requests.Session, url: str) -> list[dict[str, Any]]:
    match = re.search(r"github\.com/([^/]+/[^/#?]+)", url)
    if not match:
        return []
    repo = match.group(1).rstrip(".git")
    payload, status = fetch_json(s, f"https://api.github.com/repos/{repo}")
    if payload is None:
        return [
            {
                "artifact_type": "github_repo",
                "artifact_id": repo,
                "artifact_title": "",
                "file_count": "",
                "file_names_preview": "",
                "probe_status": status,
            }
        ]
    contents, contents_status = fetch_json(s, f"https://api.github.com/repos/{repo}/contents")
    names = [item.get("name", "") for item in contents] if isinstance(contents, list) else []
    return [
        {
            "artifact_type": "github_repo",
            "artifact_id": repo,
            "artifact_title": payload.get("full_name", ""),
            "file_count": len(names),
            "file_names_preview": "; ".join(names[:12]),
            "probe_status": f"metadata_ok_contents_{contents_status}",
        }
    ]


def probe_plain_url(s: requests.Session, url: str) -> list[dict[str, Any]]:
    try:
        r = s.get(url, timeout=TIMEOUT, stream=True, allow_redirects=True)
        return [
            {
                "artifact_type": "plain_url",
                "artifact_id": url,
                "artifact_title": "",
                "file_count": "",
                "file_names_preview": "",
                "probe_status": f"http_{r.status_code}_{r.headers.get('content-type', '')[:40]}",
            }
        ]
    except Exception as exc:  # noqa: BLE001
        return [
            {
                "artifact_type": "plain_url",
                "artifact_id": url,
                "artifact_title": "",
                "file_count": "",
                "file_names_preview": "",
                "probe_status": f"{type(exc).__name__}: {exc}",
            }
        ]


def probe_artifact(s: requests.Session, url: str) -> list[dict[str, Any]]:
    if not url or url in {"paper/package required", "paper/article required", "paper/package not yet verified"}:
        return []
    rows: list[dict[str, Any]] = []
    for part in [p.strip() for p in str(url).split(";") if p.strip()]:
        if "dataverse.harvard.edu" in part or "doi.org/10.7910/DVN/" in part:
            rows.extend(probe_dataverse_package(s, part))
        elif "osf.io" in part:
            rows.extend(probe_osf_package(s, part))
        elif "zenodo.org" in part or "10.5281/zenodo" in part:
            rows.extend(probe_zenodo(s, part))
        elif "github.com" in part:
            rows.extend(probe_github(s, part))
        elif part.startswith("http"):
            rows.extend(probe_plain_url(s, part))
    return rows


def build_package_manifest(s: requests.Session, worklist: pd.DataFrame) -> pd.DataFrame:
    manifest_rows: list[dict[str, Any]] = []
    for _, row in worklist.iterrows():
        for col in ["data_url", "prereg_url", "result_url"]:
            for probe in probe_artifact(s, str(row.get(col, ""))):
                manifest_rows.append(
                    {
                        "row_id": row["row_id"],
                        "source_family": row["source_family"],
                        "url_role": col,
                        "url": row.get(col, ""),
                        **probe,
                    }
                )
    return pd.DataFrame(manifest_rows)


def build_unlock_status(worklist: pd.DataFrame, manifest: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in worklist.iterrows():
        probes = manifest.loc[manifest["row_id"].eq(row["row_id"])]
        metadata_ok = int(probes["probe_status"].astype(str).str.contains("metadata_ok|http_200").sum()) if not probes.empty else 0
        blocked = "; ".join(
            sorted(
                {
                    status
                    for status in probes["probe_status"].dropna().astype(str)
                    if "403" in status or "404" in status or "error" in status.lower()
                }
            )
        )
        if metadata_ok:
            unlock_status = "source_metadata_unlocked"
        elif len(probes):
            unlock_status = "source_probe_attempted_blocked_or_empty"
        else:
            unlock_status = "no_machine_probe_available"
        rows.append(
            {
                "row_id": row["row_id"],
                "source_family": row["source_family"],
                "candidate_status": row["candidate_status"],
                "unlock_status": unlock_status,
                "machine_probe_count": len(probes),
                "machine_probe_ok_count": metadata_ok,
                "blocked_probe_statuses": blocked,
                "strict_blocker": row["strict_blocker"],
                "next_action": row["next_action"],
                "prereg_url": row["prereg_url"],
                "result_url": row["result_url"],
                "data_url": row["data_url"],
            }
        )
    return pd.DataFrame(rows)


def build_native_seed_rows() -> pd.DataFrame:
    # These rows are deliberately native-panel seeds. They are not appended to
    # strict Plot 3 because the D conversion is not yet defensible.
    rows = [
        {
            "row_id": "egap_mk1_vote_choice_good_news",
            "paper_or_project": "Metaketa I pooled information/accountability",
            "source_family": "EGAP Metaketa I",
            "planned_outcome_label": "Vote choice, good news",
            "estimate": 0.0004,
            "se": 0.015,
            "analytic_n": 13196,
            "cluster_n": "",
            "control_mean": 0.356,
            "effect_metric_native": "linear-probability pooled treatment coefficient",
            "conversion_flag": "stage_native_metric_clustered_adjusted_lpm",
            "source_table": "ScienceAdvances/tables/tab_11.1_main_effects.tex",
            "source_url": "https://raw.githubusercontent.com/egap/metaketa-i/main/ScienceAdvances/tables/tab_11.1_main_effects.tex",
            "promotion_recommendation": "native_panel_seed",
        },
        {
            "row_id": "egap_mk1_vote_choice_bad_news",
            "paper_or_project": "Metaketa I pooled information/accountability",
            "source_family": "EGAP Metaketa I",
            "planned_outcome_label": "Vote choice, bad news",
            "estimate": -0.003,
            "se": 0.015,
            "analytic_n": 12531,
            "cluster_n": "",
            "control_mean": 0.398,
            "effect_metric_native": "linear-probability pooled treatment coefficient",
            "conversion_flag": "stage_native_metric_clustered_adjusted_lpm",
            "source_table": "ScienceAdvances/tables/tab_11.1_main_effects.tex",
            "source_url": "https://raw.githubusercontent.com/egap/metaketa-i/main/ScienceAdvances/tables/tab_11.1_main_effects.tex",
            "promotion_recommendation": "native_panel_seed",
        },
        {
            "row_id": "egap_mk1_turnout_good_news",
            "paper_or_project": "Metaketa I pooled information/accountability",
            "source_family": "EGAP Metaketa I",
            "planned_outcome_label": "Turnout, good news",
            "estimate": 0.002,
            "se": 0.013,
            "analytic_n": 14500,
            "cluster_n": "",
            "control_mean": 0.843,
            "effect_metric_native": "linear-probability pooled treatment coefficient",
            "conversion_flag": "stage_native_metric_clustered_adjusted_lpm",
            "source_table": "ScienceAdvances/tables/tab_11.1_main_effects.tex",
            "source_url": "https://raw.githubusercontent.com/egap/metaketa-i/main/ScienceAdvances/tables/tab_11.1_main_effects.tex",
            "promotion_recommendation": "native_panel_seed",
        },
        {
            "row_id": "egap_mk1_turnout_bad_news",
            "paper_or_project": "Metaketa I pooled information/accountability",
            "source_family": "EGAP Metaketa I",
            "planned_outcome_label": "Turnout, bad news",
            "estimate": 0.018,
            "se": 0.012,
            "analytic_n": 13148,
            "cluster_n": "",
            "control_mean": 0.835,
            "effect_metric_native": "linear-probability pooled treatment coefficient",
            "conversion_flag": "stage_native_metric_clustered_adjusted_lpm",
            "source_table": "ScienceAdvances/tables/tab_11.1_main_effects.tex",
            "source_url": "https://raw.githubusercontent.com/egap/metaketa-i/main/ScienceAdvances/tables/tab_11.1_main_effects.tex",
            "promotion_recommendation": "native_panel_seed",
        },
        {
            "row_id": "egap_mk1_vote_choice_overall",
            "paper_or_project": "Metaketa I pooled information/accountability",
            "source_family": "EGAP Metaketa I",
            "planned_outcome_label": "Vote choice, overall",
            "estimate": 0.003,
            "se": 0.010,
            "analytic_n": 25820,
            "cluster_n": "",
            "control_mean": 0.369,
            "effect_metric_native": "linear-probability pooled treatment coefficient",
            "conversion_flag": "stage_native_metric_clustered_adjusted_lpm",
            "source_table": "ScienceAdvances/tables/tab_11.1_main_effects.tex",
            "source_url": "https://raw.githubusercontent.com/egap/metaketa-i/main/ScienceAdvances/tables/tab_11.1_main_effects.tex",
            "promotion_recommendation": "native_panel_seed",
        },
        {
            "row_id": "egap_mk1_turnout_overall",
            "paper_or_project": "Metaketa I pooled information/accountability",
            "source_family": "EGAP Metaketa I",
            "planned_outcome_label": "Turnout, overall",
            "estimate": 0.017,
            "se": 0.008,
            "analytic_n": 27737,
            "cluster_n": "",
            "control_mean": 0.837,
            "effect_metric_native": "linear-probability pooled treatment coefficient",
            "conversion_flag": "stage_native_metric_clustered_adjusted_lpm",
            "source_table": "ScienceAdvances/tables/tab_11.1_main_effects.tex",
            "source_url": "https://raw.githubusercontent.com/egap/metaketa-i/main/ScienceAdvances/tables/tab_11.1_main_effects.tex",
            "promotion_recommendation": "native_panel_seed",
        },
        {
            "row_id": "tess_graham1155_support_undemocratic_copartisan",
            "paper_or_project": "A Conditional Commitment? Partisan Identity and Support for Democracy in the United States",
            "source_family": "TESS",
            "planned_outcome_label": "Support for undemocratic co-partisans",
            "estimate": -0.007,
            "se": 0.008,
            "analytic_n": 4027,
            "cluster_n": "",
            "control_mean": "",
            "effect_metric_native": "covariate-adjusted coefficient from TESS results page",
            "conversion_flag": "stage_native_metric_missing_sd_or_event_counts",
            "source_table": "TESS study results summary",
            "source_url": "https://tessexperiments.org/study/graham1155",
            "promotion_recommendation": "native_panel_seed",
        },
        {
            "row_id": "tess_graham1155_manipulation_check",
            "paper_or_project": "A Conditional Commitment? Partisan Identity and Support for Democracy in the United States",
            "source_family": "TESS",
            "planned_outcome_label": "Manipulation check",
            "estimate": 0.042,
            "se": 0.027,
            "analytic_n": 4027,
            "cluster_n": "",
            "control_mean": "",
            "effect_metric_native": "covariate-adjusted coefficient from TESS results page",
            "conversion_flag": "sidecar_not_primary_outcome",
            "source_table": "TESS study results summary",
            "source_url": "https://tessexperiments.org/study/graham1155",
            "promotion_recommendation": "native_sidecar_only",
        },
        {
            "row_id": "good_politicians_filing_social",
            "paper_or_project": "Good Politicians: Experimental Evidence on Motivations for Political Candidacy and Government Performance",
            "source_family": "AEA/Zenodo",
            "planned_outcome_label": "Filing papers, social treatment versus neutral",
            "estimate": 0.010,
            "se": 0.008,
            "analytic_n": 9310,
            "cluster_n": 192,
            "control_mean": 0.030,
            "effect_metric_native": "clustered linear-probability coefficient",
            "conversion_flag": "stage_native_metric_clustered_adjusted_lpm",
            "source_table": "gulzarkhan20240105.zip replication/tables/tab1.tex",
            "source_url": "https://doi.org/10.5281/zenodo.10086096",
            "promotion_recommendation": "native_panel_seed",
        },
        {
            "row_id": "good_politicians_filing_personal",
            "paper_or_project": "Good Politicians: Experimental Evidence on Motivations for Political Candidacy and Government Performance",
            "source_family": "AEA/Zenodo",
            "planned_outcome_label": "Filing papers, personal treatment versus neutral",
            "estimate": -0.009,
            "se": 0.006,
            "analytic_n": 9310,
            "cluster_n": 192,
            "control_mean": 0.030,
            "effect_metric_native": "clustered linear-probability coefficient",
            "conversion_flag": "stage_native_metric_clustered_adjusted_lpm",
            "source_table": "gulzarkhan20240105.zip replication/tables/tab1.tex",
            "source_url": "https://doi.org/10.5281/zenodo.10086096",
            "promotion_recommendation": "native_panel_seed",
        },
        {
            "row_id": "good_politicians_elected_social",
            "paper_or_project": "Good Politicians: Experimental Evidence on Motivations for Political Candidacy and Government Performance",
            "source_family": "AEA/Zenodo",
            "planned_outcome_label": "Elected, social treatment versus neutral",
            "estimate": 0.005,
            "se": 0.005,
            "analytic_n": 9310,
            "cluster_n": 192,
            "control_mean": 0.017,
            "effect_metric_native": "clustered linear-probability coefficient",
            "conversion_flag": "stage_native_metric_clustered_adjusted_lpm",
            "source_table": "gulzarkhan20240105.zip replication/tables/tab1.tex",
            "source_url": "https://doi.org/10.5281/zenodo.10086096",
            "promotion_recommendation": "native_panel_seed",
        },
        {
            "row_id": "good_politicians_elected_personal",
            "paper_or_project": "Good Politicians: Experimental Evidence on Motivations for Political Candidacy and Government Performance",
            "source_family": "AEA/Zenodo",
            "planned_outcome_label": "Elected, personal treatment versus neutral",
            "estimate": -0.007,
            "se": 0.003,
            "analytic_n": 9310,
            "cluster_n": 192,
            "control_mean": 0.017,
            "effect_metric_native": "clustered linear-probability coefficient",
            "conversion_flag": "stage_native_metric_clustered_adjusted_lpm",
            "source_table": "gulzarkhan20240105.zip replication/tables/tab1.tex",
            "source_url": "https://doi.org/10.5281/zenodo.10086096",
            "promotion_recommendation": "native_panel_seed",
        },
    ]
    return pd.DataFrame(rows)


def chinn_from_counts(t_event: int, t_nonevent: int, c_event: int, c_nonevent: int) -> tuple[float, float]:
    values = [float(t_event), float(t_nonevent), float(c_event), float(c_nonevent)]
    if any(value == 0 for value in values):
        values = [value + 0.5 for value in values]
    a, b, c, d = values
    scale = math.sqrt(3) / math.pi
    log_or = math.log((a / b) / (c / d))
    se = (sum(1 / value for value in values) ** 0.5) * scale
    return float(log_or * scale), float(se)


def build_mousa_d_candidates() -> pd.DataFrame:
    base = RAW_DIR / "zenodo" / "3942437"
    if not (base / "wave-2.csv").exists():
        return pd.DataFrame()
    labels = {
        "own_group_preference": ("Mixed Team Sign-Up", "wave-2.csv"),
        "voted_muslim_extra": ("Vote Muslim Award", "wave-2.csv"),
        "train_t1": ("Train w/ Muslims", "waves-1-and-2.csv"),
        "attend": ("Attend Mixed Event", "waves-1-and-2.csv"),
        "went_mosul": ("Visit Mosul", "mosul-outcome-wave-2.csv"),
        "donate_t1_new1": ("Donate Mixed NGO", "wave-2.csv"),
        "dv_secular_t1": ("National Unity", "wave-2.csv"),
        "dv_neigh_t1": ("Muslim Neighbor", "wave-2.csv"),
        "dv_blame_t1": ("Muslim Blame", "wave-2.csv"),
    }
    rows = []
    for outcome, (label, filename) in labels.items():
        data = pd.read_csv(base / filename)
        sub = data[["treated", outcome]].dropna()
        treated = sub.loc[sub["treated"].eq(1), outcome]
        control = sub.loc[sub["treated"].eq(0), outcome]
        unique_values = set(sub[outcome].dropna().unique())
        if unique_values.issubset({0, 1}):
            t_event = int(treated.sum())
            t_nonevent = int(len(treated) - t_event)
            c_event = int(control.sum())
            c_nonevent = int(len(control) - c_event)
            d_value, se_value = chinn_from_counts(t_event, t_nonevent, c_event, c_nonevent)
            method = "chinn_log_or_to_d_from_event_counts"
        else:
            control_sd = float(control.std(ddof=1))
            d_value = float((treated.mean() - control.mean()) / control_sd)
            se_value = float(
                (
                    (len(treated) + len(control)) / (len(treated) * len(control))
                    + d_value**2 / (2 * (len(treated) + len(control) - 2))
                )
                ** 0.5
            )
            method = "mean_difference_over_control_sd"
        rows.append(
            {
                "row_id": f"mousa2020_{outcome}",
                "outcome": outcome,
                "outcome_label": label,
                "source_file": filename,
                "n_treatment": len(treated),
                "n_control": len(control),
                "analytic_n": len(sub),
                "control_mean": float(control.mean()),
                "treated_mean": float(treated.mean()),
                "D_candidate": d_value,
                "abs_D_candidate": abs(d_value),
                "D_se_approx": se_value,
                "conversion_method": method,
            }
        )
    out = pd.DataFrame(rows)
    out.loc[len(out)] = {
        "row_id": "mousa2020_paper_median_main_outcomes",
        "outcome": "paper_median",
        "outcome_label": "Median of nine main behavioral/attitudinal outcomes",
        "source_file": "main-analyses.R outcome set",
        "n_treatment": "",
        "n_control": "",
        "analytic_n": float(out["analytic_n"].median()),
        "control_mean": "",
        "treated_mean": "",
        "D_candidate": float(out["abs_D_candidate"].median()),
        "abs_D_candidate": float(out["abs_D_candidate"].median()),
        "D_se_approx": "",
        "conversion_method": "paper_median_abs_D",
    }
    return out


def build_user_todos(worklist: pd.DataFrame, status: pd.DataFrame, aea_queue: pd.DataFrame) -> pd.DataFrame:
    todo_rows = [
        {
            "priority": 1,
            "todo_id": "manual_extract_aea_governance_queue",
            "source_family": "AEA RCT Registry",
            "task": "Work through the compact AEA governance candidate queue and extract one PAP-matched focal estimate/SE/N from each linked paper or replication package.",
            "url": "https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/OHBI3I",
            "local_file": str(AEA_GOVERNANCE_OUT.relative_to(ROOT)),
            "why_user_needed": f"{len(aea_queue)} link-ready governance/political candidates were found; effect rows are in linked papers/packages, not in the registry CSV.",
        },
        {
            "priority": 2,
            "todo_id": "manual_extract_exact_zenodo_models",
            "source_family": "Zenodo packages",
            "task": "Use the downloaded Zenodo packages to replace native/raw reconstructions with exact published covariate-adjusted model rows where needed.",
            "url": "https://doi.org/10.5281/zenodo.10086096 ; https://zenodo.org/records/3942437 ; https://zenodo.org/records/17792605",
            "local_file": "data/raw/corpus_candidates/political_science_unlock/zenodo/",
            "why_user_needed": "Zenodo metadata and the small Mousa/Good Politicians packages are now locally downloaded; remaining work is selector/model extraction, not URL access.",
        },
        {
            "priority": 3,
            "todo_id": "manual_extract_metaketa_iii_iv",
            "source_family": "EGAP Metaketa III/IV",
            "task": "Extract component/native rows only if a separate native panel is desired; pooled Metaketa III/IV rows are already in strict Plot 3.",
            "url": "https://osf.io/knje7/ ; https://osf.io/2juyz/ ; https://osf.io/jdgf4",
            "local_file": str(PACKAGE_MANIFEST_OUT.relative_to(ROOT)),
            "why_user_needed": "The headline pooled dots are already included; this TODO is only for optional component-study/native panels and double-count-safe child rows.",
        },
        {
            "priority": 4,
            "todo_id": "manual_download_tess_roper_data",
            "source_family": "TESS",
            "task": "For TESS rows, fetch Roper/OSF data where the OSF API shows empty roots and reconstruct event counts or outcome SDs for D conversion.",
            "url": "https://tessexperiments.org/study/graham1155 ; https://tessexperiments.org/study/johnson1389 ; https://tessexperiments.org/study/jackson002",
            "local_file": str(NATIVE_SEEDS_OUT.relative_to(ROOT)),
            "why_user_needed": "The TESS pages expose N and some native results, but not arm event counts/outcome SDs required for defensible D conversion.",
        },
        {
            "priority": 5,
            "todo_id": "manual_confirm_metaketa_ii_pooled",
            "source_family": "EGAP Metaketa II",
            "task": "Confirm final pooled-paper/package status and extract native tax compliance/formalization ATE/SE/N rows.",
            "url": "https://egap.org/our-work/the-metaketa-initiative/roundtwo-taxation/",
            "local_file": str(UNLOCK_STATUS_OUT.relative_to(ROOT)),
            "why_user_needed": "The PAP architecture is clear, but the final pooled package was not machine-verified to the same standard as Metaketa I/III/IV.",
        },
        {
            "priority": 6,
            "todo_id": "manual_openicpsr_terms",
            "source_family": "OpenICPSR / Metaketa II",
            "task": "Open OpenICPSR pages that may require click-through terms and extract the matched registry/PAP plus primary tax-compliance coefficient/SE/N.",
            "url": "https://www.openicpsr.org/openicpsr/project/147561/version/V1/view",
            "local_file": "",
            "why_user_needed": "The landing page is visible, but package download/selector matching is still a manual rescue step.",
        },
    ]
    blocked = status.loc[status["unlock_status"].eq("source_probe_attempted_blocked_or_empty")]
    for _, row in blocked.iterrows():
        todo_rows.append(
            {
                "priority": 10,
                "todo_id": f"blocked_probe_{row['row_id']}",
                "source_family": row["source_family"],
                "task": row["next_action"],
                "url": " ; ".join(
                    str(row.get(col, ""))
                    for col in ["prereg_url", "result_url", "data_url"]
                    if str(row.get(col, "")).startswith("http")
                ),
                "local_file": str(UNLOCK_STATUS_OUT.relative_to(ROOT)),
                "why_user_needed": row["blocked_probe_statuses"] or row["strict_blocker"],
            }
        )
    return pd.DataFrame(todo_rows).sort_values(["priority", "todo_id"]).reset_index(drop=True)


def clean_for_csv(df: pd.DataFrame) -> pd.DataFrame:
    def clean_cell(value: object) -> object:
        if not isinstance(value, str):
            return value
        without_cr = value.replace("\r", "")
        return "\n".join(line.rstrip(" \t") for line in without_cr.split("\n"))

    if hasattr(df, "map"):
        return df.map(clean_cell)
    return df.applymap(clean_cell)


def write_csv(df: pd.DataFrame, path: Path) -> None:
    clean_for_csv(df).to_csv(path, index=False, lineterminator="\n")


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    s = session()
    metadata = ensure_aea_snapshot(s)
    worklist = pd.read_csv(WORKLIST)
    aea_queue = build_aea_governance_queue()
    manifest = build_package_manifest(s, worklist)
    status = build_unlock_status(worklist, manifest)
    native = build_native_seed_rows()
    mousa = build_mousa_d_candidates()
    todos = build_user_todos(worklist, status, aea_queue)

    write_csv(aea_queue, AEA_GOVERNANCE_OUT)
    write_csv(manifest, PACKAGE_MANIFEST_OUT)
    write_csv(status, UNLOCK_STATUS_OUT)
    write_csv(native, NATIVE_SEEDS_OUT)
    write_csv(mousa, MOUSA_D_CANDIDATES_OUT)
    write_csv(todos, TODO_OUT)

    print(f"AEA snapshot: {metadata_title(metadata)}")
    print(f"AEA governance candidates: {len(aea_queue)} -> {AEA_GOVERNANCE_OUT}")
    print(f"Package/API manifest rows: {len(manifest)} -> {PACKAGE_MANIFEST_OUT}")
    print(f"Unlock status rows: {len(status)} -> {UNLOCK_STATUS_OUT}")
    print(f"Native metric seed rows: {len(native)} -> {NATIVE_SEEDS_OUT}")
    print(f"Mousa D candidates: {len(mousa)} -> {MOUSA_D_CANDIDATES_OUT}")
    print(f"User TODO rows: {len(todos)} -> {TODO_OUT}")


if __name__ == "__main__":
    main()
