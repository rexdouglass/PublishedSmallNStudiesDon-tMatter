#!/usr/bin/env python3
"""Build a non-lossy replication-source audit from every current tracking surface."""

from __future__ import annotations

import math
import re
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DERIVED = ROOT / "data" / "derived" / "replication_pairs"
HARVEST = DERIVED / "harvest"
STAGED = HARVEST / "staged"
PROMOTED = HARVEST / "promoted"
RAW_LEADS = ROOT / "data" / "raw" / "replication_projects" / "lead_harvest"
REPORTS = ROOT / "reports"

MANIFEST = HARVEST / "harvest_manifest.csv"
QUEUE = HARVEST / "lead_queue_status.csv"
SOURCE_CATALOG = DERIVED / "replication_pair_source_catalog.csv"
ALL_PAIRS = DERIVED / "replication_pairs_all_on_hand.csv"

OUT_AUDIT = DERIVED / "replication_source_audit.csv"
OUT_INVENTORY = DERIVED / "replication_source_evidence_inventory.csv"
OUT_WORKLIST = DERIVED / "replication_source_worklist.csv"
OUT_MD = REPORTS / "replication_source_audit.md"


ALIAS_RULES: list[dict[str, object]] = [
    {
        "canonical_source_id": "family::fred",
        "canonical_label": "FReD filtered pair table",
        "patterns": [
            r"fred[_ ]filtered[_ ]pair[_ ]table",
            r"\bfred[_ ]core\b",
            r"\bfred[_ ]curatescience\b",
            r"\bfred[_ ]forrt\b",
            r"\bfred[_ ]openmkt\b",
            r"\bfred[_ ]sosci[_ ]submissions\b",
            r"\bfred[_ ]new[_ ]rrr\b",
            r"\bfred[_ ]other[_ ]additions\b",
            r"fred[_ ]diff[_ ]2024",
            r"fred differential-effects supplement",
        ],
    },
    {
        "canonical_source_id": "family::score_project",
        "canonical_label": "SCORE analyst join",
        "patterns": [r"score[_ ]analyst[_ ]join", r"tyner[_ ]nosek[_ ]2026", r"\bscore project\b"],
    },
    {
        "canonical_source_id": "family::rpcb",
        "canonical_label": "RPCB",
        "patterns": [r"\brpcb\b", r"rpcb[_ ]e5nvr", r"reproducibility project: cancer biology"],
    },
    {
        "canonical_source_id": "family::251_rescue_projects",
        "canonical_label": "251 Rescue parsed data",
        "patterns": [r"251[_ ]rescue", r"rescue17[_ ]28classics", r"\brescue projects\b"],
    },
    {
        "canonical_source_id": "family::eqipd_open_field",
        "canonical_label": "EQIPD stagewise open-field lab contrasts",
        "patterns": [r"eqipd[_ ]2022", r"eqipd stagewise open[-_ ]field lab contrasts"],
    },
    {
        "canonical_source_id": "family::pipeline_project",
        "canonical_label": "Pipeline supplement + packet data",
        "patterns": [
            r"pipeline supplement \+ packet data",
            r"\bpipeline project\b",
            r"independent[_ ]replication[_ ]initiative",
            r"pre[- ]publication independent replication",
        ],
    },
    {
        "canonical_source_id": "family::awesome_replicability_data",
        "canonical_label": "Awesome replicability-data repository",
        "patterns": [
            r"awesome[_ ]replicability[_ ]paired[_ ]raw[_ ]csvs",
            r"awesome[_ ]lie[_ ]language",
            r"awesome[_ ]mindbody[_ ]selfcentrality",
            r"awesome[_ ]cleanliness[_ ]moral",
            r"awesome[_ ]emdr[_ ]misinfo",
            r"awesome[_ ]pain[_ ]coop",
            r"awesome[_ ]pain[_ ]tolerance",
            r"awesome[_ ]body[_ ]dissatisfaction",
            r"awesome[_ ]climate[_ ]misinfo",
            r"awesome[_ ]priming[_ ]exercise",
            r"awesome[_ ]queue",
            r"awesome[_ ]time[_ ]honest",
            r"lie and language",
            r"mind body self centrality",
            r"cleanliness and moral judgment",
            r"emdr and misinformation",
            r"pain and cooperation",
            r"pain tolerance direct replication",
            r"body dissatisfaction direct replication",
            r"climate misinformation direct replication",
            r"priming and exercise direct replication",
            r"queue design and worker productivity",
            r"honesty and time pressure",
        ],
    },
    {
        "canonical_source_id": "family::transparent_psi_project",
        "canonical_label": "Transparent Psi Project",
        "patterns": [r"transparent psi project", r"tpp[_ ]bem"],
    },
    {
        "canonical_source_id": "family::manybabies_3",
        "canonical_label": "ManyBabies 3",
        "patterns": [r"manybabies[_ ]3", r"manybabies 3"],
    },
    {
        "canonical_source_id": "family::news_discernment_replication",
        "canonical_label": "News discernment replication",
        "patterns": [r"news[_ ]discernment[_ ]replication", r"news discernment"],
    },
    {
        "canonical_source_id": "family::eyewitness_ten_countries_2018",
        "canonical_label": "Eyewitness memory distortion in ten countries",
        "patterns": [
            r"eyewitness[_ ]ten[_ ]countries",
            r"eyewitness memory distortion",
            r"garry.*cowitness",
            r"ito et al.*2018",
        ],
    },
    {
        "canonical_source_id": "family::ying_2023_pilot_full_scale_trials",
        "canonical_label": "Ying 2023 pilot-full-scale trials",
        "patterns": [r"\bying[_ ]2023\b", r"ying 2023 manual partial reconstruction", r"ying_2023_pair_roster"],
    },
    {
        "canonical_source_id": "family::protzko_nhb_2023",
        "canonical_label": "Protzko 2023 NHB",
        "patterns": [r"protzko.*nhb", r"nhb.*protzko"],
    },
    {
        "canonical_source_id": "family::communication_privacy_2025",
        "canonical_label": "Communication privacy replication corpus",
        "patterns": [r"communication[_ ]privacy", r"communication privacy"],
    },
    {
        "canonical_source_id": "family::contextual_bias_2026",
        "canonical_label": "Contextual bias in verbal credibility assessment",
        "patterns": [r"contextual[_ ]bias", r"contextual bias in verbal credibility"],
    },
    {
        "canonical_source_id": "family::deceptive_intentions_2018",
        "canonical_label": "Deceptive intentions verbal credibility replication",
        "patterns": [r"deceptive[_ ]intentions", r"deceptive intentions verbal credibility"],
    },
    {
        "canonical_source_id": "family::covid_online_2021",
        "canonical_label": "COVID online experiment replications",
        "patterns": [r"covid[_ ]online", r"covid online experiment replications"],
    },
    {
        "canonical_source_id": "family::linguistic_frame_liability",
        "canonical_label": "Linguistic frame effect on blame and liability",
        "patterns": [r"linguistic[_ ]frame[_ ]liability", r"linguistic frame effect on blame and liability"],
    },
    {
        "canonical_source_id": "family::public_admin_blame",
        "canonical_label": "Public-administration blame experiment replication",
        "patterns": [
            r"public[_ -]admin.*blame",
            r"public[- ]administration blame",
            r"citizens'? blame of politicians",
        ],
    },
    {
        "canonical_source_id": "family::online_image_credibility",
        "canonical_label": "Online image credibility",
        "patterns": [r"online[_ ]image[_ ]credibility", r"online image credibility"],
    },
    {
        "canonical_source_id": "family::greed_ses_2016",
        "canonical_label": "Greed by SES replications",
        "patterns": [r"greed[_ ]ses", r"greed by ses"],
    },
    {
        "canonical_source_id": "family::retrieval_extinction_rats_2017",
        "canonical_label": "Retrieval extinction fear conditioning in rats",
        "patterns": [r"retrieval[_ ]extinction[_ ]rats", r"retrieval extinction fear conditioning in rats"],
    },
    {
        "canonical_source_id": "family::wood_scaffolding_2025",
        "canonical_label": "Wood scaffolding direct replication",
        "patterns": [r"wood[_ ]scaffolding", r"wood scaffolding direct replication"],
    },
    {
        "canonical_source_id": "family::awesome_lie_language",
        "canonical_label": "Lie and language",
        "patterns": [r"awesome[_ ]lie[_ ]language", r"\blie and language\b"],
    },
    {
        "canonical_source_id": "family::awesome_mindbody_selfcentrality",
        "canonical_label": "Mind body self centrality",
        "patterns": [r"awesome[_ ]mindbody[_ ]selfcentrality", r"mind body self centrality"],
    },
    {
        "canonical_source_id": "family::psa_002_object_orientation",
        "canonical_label": "PSA 002 object orientation",
        "patterns": [r"psa[_ ]002[_ ]object[_ ]orientation", r"object orientation lab rows"],
    },
    {
        "canonical_source_id": "family::psa_006_trolley",
        "canonical_label": "PSA 006 trolley Greene",
        "patterns": [r"psa[_ ]006[_ ]trolley", r"trolley country rows"],
    },
    {
        "canonical_source_id": "family::psa_004_turri",
        "canonical_label": "PSA 004 JTB Turri",
        "patterns": [r"psa[_ ]004", r"jtb[_ ]turri", r"turri.*darrel", r"justified[- ]true[- ]belief"],
    },
    {
        "canonical_source_id": "family::rrr_bouwmeester_2017",
        "canonical_label": "RRR Bouwmeester 2017",
        "patterns": [r"rrr[_ ]bouwmeester[_ ]2017", r"bouwmeester 2017"],
    },
    {
        "canonical_source_id": "family::rrr_cheung_2016",
        "canonical_label": "RRR Cheung 2016",
        "patterns": [r"rrr[_ ]cheung[_ ]2016", r"cheung 2016"],
    },
    {
        "canonical_source_id": "family::rrr_colling_2020",
        "canonical_label": "RRR Colling 2020",
        "patterns": [r"rrr[_ ]colling[_ ]2020", r"colling 2020", r"\bsnarc\b"],
    },
    {
        "canonical_source_id": "family::rrr_elliott_2021",
        "canonical_label": "RRR Elliott 2021",
        "patterns": [r"rrr[_ ]elliott[_ ]2021", r"elliott 2021 aggregate table"],
    },
    {
        "canonical_source_id": "family::rrr_mccarthy_2018",
        "canonical_label": "RRR McCarthy 2018",
        "patterns": [r"rrr[_ ]mccarthy[_ ]2018", r"mccarthy 2018"],
    },
    {
        "canonical_source_id": "family::rrr_verschuere_2018",
        "canonical_label": "RRR Verschuere 2018",
        "patterns": [r"rrr[_ ]verschuere[_ ]2018", r"verschuere 2018"],
    },
    {
        "canonical_source_id": "family::management_science_replication_project",
        "canonical_label": "Management Science Replication Project",
        "patterns": [r"\bmsrp[_ ]om[_ ]2023\b", r"management science replication project", r"\bmsrp_"],
    },
]


def slugify(text: object) -> str:
    s = str(text or "").strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_")


def normalize_stage_base(path: Path) -> str:
    name = path.name
    name = re.sub(r"__stage\.csv$", "", name)
    name = re.sub(r"__promoted_pairs\.csv$", "", name)
    return name


def read_csv_safe(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def read_json_safe(path: Path) -> object:
    try:
        import json

        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def first_nonempty(values: list[object]) -> str:
    for value in values:
        if value is None:
            continue
        s = str(value).strip()
        if s and s.lower() != "nan":
            return s
    return ""


def humanize_source_handle(value: object) -> str:
    text = str(value or "").strip()
    for prefix in ["lead::", "artifact::", "source::"]:
        if text.startswith(prefix):
            text = text.split(prefix, 1)[1]
            break
    if "|" in text:
        text = text.split("|")[-1]
    text = re.sub(r"[_-]+", " ", text).strip()
    token_map = {
        "bwas": "BWAS",
        "eeg": "EEG",
        "eef": "EEF",
        "egap": "EGAP",
        "ern": "ERN",
        "fmri": "fMRI",
        "ibl": "IBL",
        "ies": "IES",
        "jtb": "JTB",
        "nhb": "NHB",
        "osf": "OSF",
        "pe": "Pe",
        "psa": "PSA",
        "rpcb": "RPCB",
        "rrr": "RRR",
    }
    words = []
    for word in text.split():
        lowered = word.lower()
        words.append(token_map.get(lowered, word[:1].upper() + word[1:]))
    return " ".join(words)


def is_internal_handle(value: object) -> bool:
    text = str(value or "").strip()
    return text.startswith(("lead::", "artifact::", "source::"))


def bool_any(values: list[object]) -> bool:
    return any(bool(v) for v in values)


def summarize_columns(df: pd.DataFrame, limit: int = 12) -> str:
    cols = list(df.columns)
    if len(cols) <= limit:
        return ", ".join(cols)
    return ", ".join(cols[:limit]) + ", ..."


def detect_stage_kind(df: pd.DataFrame) -> str:
    cols = set(df.columns)
    if {"lead_id", "project", "terminal_status"} <= cols:
        return "lead_status_snapshot"
    if {"pair_id", "D_original", "D_replication", "N_original", "N_replication"} <= cols:
        return "pair_table_with_d"
    if {"promotion_decision", "analytic_status"} <= cols:
        return "manual_partial_reconstruction"
    if {"pair_number", "pilot_citation_text", "full_scale_citation_text"} <= cols:
        return "pair_roster"
    if {"source_dataset", "source_paper", "pair_id"} <= cols:
        return "structured_pair_notes"
    return "generic_stage_csv"


def summarize_stage_notes(df: pd.DataFrame) -> str:
    pieces: list[str] = []
    if "promotion_decision" in df.columns:
        counts = df["promotion_decision"].fillna("").astype(str).value_counts()
        if not counts.empty:
            pieces.append(
                "promotion_decision="
                + "; ".join(f"{idx}:{int(val)}" for idx, val in counts.items() if str(idx).strip())
            )
    if "analytic_status" in df.columns:
        counts = df["analytic_status"].fillna("").astype(str).value_counts()
        if not counts.empty:
            pieces.append(
                "analytic_status="
                + "; ".join(f"{idx}:{int(val)}" for idx, val in counts.items() if str(idx).strip())
            )
    if "promotion_blocker" in df.columns:
        blockers = sorted({str(x).strip() for x in df["promotion_blocker"].dropna() if str(x).strip()})
        if blockers:
            pieces.append("promotion_blocker=" + " | ".join(blockers[:5]))
    return "; ".join(pieces)


def summarize_raw_dir(path: Path) -> dict[str, object]:
    files = sorted([p.name for p in path.iterdir() if p.is_file()])
    dirs = sorted([p.name for p in path.iterdir() if p.is_dir()])
    names = files + dirs
    provider_hints = []
    for prefix, code in [
        ("osf_", "osf"),
        ("github_", "github"),
        ("dataverse_", "dataverse"),
        ("manual__", "manual"),
        ("raw__", "direct_raw"),
    ]:
        if any(name.startswith(prefix) for name in names):
            provider_hints.append(code)
    if "osf_manifest.json" in files:
        provider_hints.append("osf_manifest")
    if "github_contents_manifest.json" in files:
        provider_hints.append("github_manifest")

    metadata_name_patterns = [
        r"landing_(probe|preview)\.",
        r"raw_(probe|preview|download)\.",
        r".*_download\.json$",
        r".*_manifest\.json$",
        r".*_file_list\.csv$",
    ]

    def is_metadata_file(name: str) -> bool:
        return any(re.search(pattern, name) for pattern in metadata_name_patterns)

    def looks_like_failed_download(name: str) -> bool:
        if not re.search(r"\.(csv|xls|xlsx|sav|rda|rdata|tab|zip|pdf|mat)$", name, re.I):
            return False
        path_obj = path / name
        if path_obj.stat().st_size > 4096:
            return False
        try:
            preview = path_obj.read_text(encoding="utf-8", errors="ignore")[:500].lower()
        except Exception:
            return False
        return (
            '"status":"error"' in preview
            or '"status": "error"' in preview
            or '"code":403' in preview
            or '"code": 403' in preview
            or "not authorized to access this object" in preview
            or "<!doctype html" in preview
        )

    payload_files = [name for name in files if not is_metadata_file(name) and not looks_like_failed_download(name)]

    landing_status = ""
    landing_url = ""
    landing_probe = path / "landing_probe.json"
    if landing_probe.exists():
        probe = read_json_safe(landing_probe)
        if isinstance(probe, dict):
            landing_status = str(probe.get("status_code", "")).strip()
            landing_url = str(probe.get("final_url", "")).strip() or str(probe.get("url", "")).strip()

    if payload_files or dirs:
        raw_payload_status = "downloaded_payload_present"
    elif any(name.endswith("_manifest.json") or name.endswith("_file_list.csv") for name in files):
        raw_payload_status = "manifest_only"
    elif landing_status and landing_status not in {"200", "301", "302"}:
        raw_payload_status = "landing_probe_blocked"
    else:
        raw_payload_status = "landing_probe_only"

    return {
        "raw_file_count": len(files),
        "raw_subdir_count": len(dirs),
        "raw_payload_status": raw_payload_status,
        "raw_provider_hints": " | ".join(sorted(set(provider_hints))),
        "landing_status_code": landing_status,
        "landing_final_url": landing_url,
        "raw_dir_summary": ", ".join(names[:12]),
    }


def match_alias_rule(text: str) -> tuple[str, str, str]:
    text = text.lower()
    for rule in ALIAS_RULES:
        for pattern in rule["patterns"]:
            if re.search(str(pattern), text):
                return (
                    str(rule["canonical_source_id"]),
                    str(rule["canonical_label"]),
                    str(pattern),
                )
    return "", "", ""


def assign_canonical_source(row: pd.Series) -> tuple[str, str, str, str]:
    text = " | ".join(
        [
            str(row.get("source_handle", "")),
            str(row.get("project", "")),
            str(row.get("source_dataset", "")),
            str(row.get("evidence_key", "")),
            str(row.get("path", "")),
            str(row.get("notes", "")),
        ]
    )
    canonical_source_id, canonical_label, alias_rule = match_alias_rule(text)
    if canonical_source_id:
        return canonical_source_id, canonical_label, alias_rule, "manual_pattern"

    source_handle = str(row.get("source_handle", "")).strip()
    source_dataset = first_nonempty([row.get("source_dataset")])
    project = first_nonempty([row.get("project")])
    canonical_label = first_nonempty([source_dataset, project, source_handle])
    if is_internal_handle(canonical_label):
        canonical_label = humanize_source_handle(canonical_label)
    return source_handle, canonical_label, "identity", "identity"


def normalize_blocker_codes(text: str) -> list[str]:
    text = str(text or "").lower()
    codes: list[str] = []
    pattern_map = [
        (r"parser_family_not_implemented", "parser_not_implemented"),
        (r"effect_conversion_policy_missing", "conversion_policy_missing"),
        (r"\bnon_d_metric\b|metric_not_on_shared_d_axis", "metric_not_on_shared_d_axis"),
        (r"native_md_only|native_metric_only", "native_metric_only"),
        (r"pilot_effect_missing", "pilot_effect_missing"),
        (r"needs_primary_pdf_confirmation", "needs_primary_pdf_confirmation"),
        (r"pilot_n_and_variance_missing", "pilot_n_and_variance_missing"),
        (r"machine_readable_pair_results|downloaded_reports_only", "missing_machine_readable_pair_results"),
        (r"missing_downloaded_pair_payload|download_missing_pair_payload|manifest_only_no_data_downloaded|zero files|no file payload", "missing_machine_readable_pair_results"),
        (r"original_side_missing|native_metric_or_original_side_missing", "original_side_missing"),
        (r"not_original_replication_pair_table|not_pair_table|source_not_pair_buildable", "source_not_pair_buildable"),
        (r"pair_roster|dissertation_pair_roster|roster-only|roster_only", "roster_only"),
        (r"overlap_or_dedup_required|overlap/deduplication unresolved|overlap risk unresolved|deduplication unresolved", "overlap_or_dedup_required"),
        (r"cross-check|cross check", "cross_check_only"),
        (r"access|cloudflare|captcha|paywall|restricted|http_403|requires_login|not authorized", "access_restriction"),
        (r"landing_probe_blocked", "access_restriction"),
        (r"endpoint mismatch|different endpoint|same primary endpoint.*false", "endpoint_mismatch"),
    ]
    for pattern, code in pattern_map:
        if re.search(pattern, text):
            codes.append(code)
    return sorted(set(codes))


def normalize_catalog_role_codes(text: str) -> list[str]:
    text = str(text or "").lower()
    codes: list[str] = []
    if "cross-check" in text or "cross check" in text:
        codes.append("catalog_cross_check_only")
    if "not used as the direct pair table" in text or "retained as a cross-check" in text:
        codes.append("catalog_cross_check_only")
    if "not a pair table" in text or "not a richer pair table" in text or "not yet pair-buildable" in text:
        codes.append("catalog_cross_check_only")
    if "sidecar" in text or "auxiliary" in text or "archival mirror" in text or "overlap" in text:
        codes.append("catalog_cross_check_only")
    if "manual" in text:
        codes.append("manual_source")
    return sorted(set(codes))


def build_live_summary() -> pd.DataFrame:
    d = read_csv_safe(ALL_PAIRS)
    if d.empty:
        return pd.DataFrame(columns=["project", "source_dataset", "live_pair_rows", "raw_file_examples"])
    grouped = (
        d.groupby(["project", "source_dataset"], dropna=False)
        .agg(
            live_pair_rows=("pair_id", "count"),
            raw_file_examples=("raw_file", lambda s: " | ".join(sorted({str(x) for x in s.dropna().astype(str)})[:3])),
        )
        .reset_index()
    )
    return grouped


def make_source_handle(project: object, source_dataset: object) -> str:
    return f"source::{slugify(project)}|{slugify(source_dataset)}"


def build_inventory() -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    manifest = read_csv_safe(MANIFEST)
    if not manifest.empty:
        for row in manifest.to_dict(orient="records"):
            lead_id = first_nonempty([row.get("lead_id")])
            rows.append(
                {
                    "source_handle": f"lead::{lead_id}",
                    "evidence_kind": "manifest_lead",
                    "evidence_key": lead_id,
                    "project": first_nonempty([row.get("project")]),
                    "source_dataset": "",
                    "path": str(MANIFEST),
                    "terminal_status": first_nonempty([row.get("terminal_status")]),
                    "promotion_blocker": first_nonempty([row.get("promotion_blocker")]),
                    "next_action": first_nonempty([row.get("next_action")]),
                    "notes": first_nonempty([row.get("notes")]),
                    "access_class": first_nonempty([row.get("access_class")]),
                    "directness_class": first_nonempty([row.get("directness_class")]),
                    "metric_class": first_nonempty([row.get("metric_class")]),
                    "integrated_in_build": False,
                    "file_rows": math.nan,
                    "usable_pair_rows": math.nan,
                    "live_pair_rows": math.nan,
                }
            )

    queue = read_csv_safe(QUEUE)
    if not queue.empty:
        for row in queue.to_dict(orient="records"):
            lead_id = first_nonempty([row.get("lead_id")])
            rows.append(
                {
                    "source_handle": f"lead::{lead_id}",
                    "evidence_kind": "queue_status",
                    "evidence_key": lead_id,
                    "project": first_nonempty([row.get("project")]),
                    "source_dataset": "",
                    "path": str(QUEUE),
                    "terminal_status": first_nonempty([row.get("terminal_status")]),
                    "promotion_blocker": first_nonempty([row.get("promotion_blocker")]),
                    "next_action": first_nonempty([row.get("next_action")]),
                    "notes": first_nonempty([row.get("notes")]),
                    "access_class": first_nonempty([row.get("access_class")]),
                    "directness_class": first_nonempty([row.get("directness_class")]),
                    "metric_class": first_nonempty([row.get("metric_class")]),
                    "integrated_in_build": False,
                    "file_rows": math.nan,
                    "usable_pair_rows": math.nan,
                    "live_pair_rows": math.nan,
                }
            )

    if RAW_LEADS.exists():
        for path in sorted(RAW_LEADS.iterdir()):
            if not path.is_dir():
                continue
            lead_id = path.name
            raw_meta = summarize_raw_dir(path)
            rows.append(
                {
                    "source_handle": f"lead::{lead_id}",
                    "evidence_kind": "raw_lead_dir",
                    "evidence_key": lead_id,
                    "project": "",
                    "source_dataset": "",
                    "path": str(path),
                    "terminal_status": "",
                    "promotion_blocker": "",
                    "next_action": "",
                    "notes": f"raw lead-harvest artifact directory present; {raw_meta['raw_payload_status']}; {raw_meta['raw_dir_summary']}",
                    "access_class": "",
                    "directness_class": "",
                    "metric_class": "",
                    "integrated_in_build": False,
                    "file_rows": math.nan,
                    "usable_pair_rows": math.nan,
                    "live_pair_rows": math.nan,
                    "raw_file_count": raw_meta["raw_file_count"],
                    "raw_subdir_count": raw_meta["raw_subdir_count"],
                    "raw_payload_status": raw_meta["raw_payload_status"],
                    "raw_provider_hints": raw_meta["raw_provider_hints"],
                    "landing_status_code": raw_meta["landing_status_code"],
                    "landing_final_url": raw_meta["landing_final_url"],
                }
            )

    if STAGED.exists():
        for path in sorted(STAGED.glob("*.csv")):
            df = read_csv_safe(path)
            base = normalize_stage_base(path)
            kind = detect_stage_kind(df) if not df.empty else "unreadable_stage_csv"
            if not df.empty and "lead_id" in df.columns:
                unique_leads = sorted({str(x).strip() for x in df["lead_id"].dropna() if str(x).strip()})
                if len(unique_leads) == 1:
                    handle = f"lead::{unique_leads[0]}"
                else:
                    handle = f"artifact::{base}"
            else:
                handle = f"artifact::{base}"
            rows.append(
                {
                    "source_handle": handle,
                    "evidence_kind": "staged_file",
                    "evidence_key": base,
                    "project": first_nonempty([df["project"].iloc[0] if not df.empty and "project" in df.columns else ""]),
                    "source_dataset": first_nonempty([df["source_dataset"].iloc[0] if not df.empty and "source_dataset" in df.columns else ""]),
                    "path": str(path),
                    "terminal_status": "",
                    "promotion_blocker": first_nonempty(
                        [
                            summarize_stage_notes(df),
                            df["promotion_blocker"].iloc[0] if not df.empty and "promotion_blocker" in df.columns else "",
                        ]
                    ),
                    "next_action": "",
                    "notes": first_nonempty(
                        [
                            f"{kind}; rows={len(df)}; cols={len(df.columns)}",
                            f"columns={summarize_columns(df)}" if not df.empty else "",
                        ]
                    ),
                    "access_class": "",
                    "directness_class": "",
                    "metric_class": "",
                    "integrated_in_build": False,
                    "file_rows": len(df),
                    "usable_pair_rows": math.nan,
                    "live_pair_rows": math.nan,
                    "raw_file_count": math.nan,
                    "raw_subdir_count": math.nan,
                    "raw_payload_status": "",
                    "raw_provider_hints": "",
                    "landing_status_code": "",
                    "landing_final_url": "",
                }
            )

    if PROMOTED.exists():
        for path in sorted(PROMOTED.glob("*.csv")):
            df = read_csv_safe(path)
            base = normalize_stage_base(path)
            project = first_nonempty([df["project"].iloc[0] if not df.empty and "project" in df.columns else ""])
            source_dataset = first_nonempty([df["source_dataset"].iloc[0] if not df.empty and "source_dataset" in df.columns else ""])
            if project or source_dataset:
                handle = make_source_handle(project, source_dataset)
            else:
                handle = f"artifact::{base}"
            rows.append(
                {
                    "source_handle": handle,
                    "evidence_kind": "promoted_file",
                    "evidence_key": base,
                    "project": project,
                    "source_dataset": source_dataset,
                    "path": str(path),
                    "terminal_status": "promoted",
                    "promotion_blocker": "",
                    "next_action": "",
                    "notes": f"promoted pair table; rows={len(df)}; cols={len(df.columns)}",
                    "access_class": "",
                    "directness_class": "",
                    "metric_class": "",
                    "integrated_in_build": True,
                    "file_rows": len(df),
                    "usable_pair_rows": len(df),
                    "live_pair_rows": math.nan,
                    "raw_file_count": math.nan,
                    "raw_subdir_count": math.nan,
                    "raw_payload_status": "",
                    "raw_provider_hints": "",
                    "landing_status_code": "",
                    "landing_final_url": "",
                }
            )

    catalog = read_csv_safe(SOURCE_CATALOG)
    if not catalog.empty:
        for row in catalog.to_dict(orient="records"):
            handle = make_source_handle(row.get("project"), row.get("source_dataset"))
            rows.append(
                {
                    "source_handle": handle,
                    "evidence_kind": "source_catalog_row",
                    "evidence_key": f"{row.get('project')}|{row.get('source_dataset')}",
                    "project": first_nonempty([row.get("project")]),
                    "source_dataset": first_nonempty([row.get("source_dataset")]),
                    "path": first_nonempty([row.get("raw_file"), str(SOURCE_CATALOG)]),
                    "terminal_status": "integrated" if bool(row.get("integrated_in_build")) else "catalog_only",
                    "promotion_blocker": "",
                    "next_action": "",
                    "notes": first_nonempty([row.get("notes")]),
                    "access_class": "",
                    "directness_class": first_nonempty([row.get("classification")]),
                    "metric_class": "",
                    "integrated_in_build": bool(row.get("integrated_in_build")),
                    "file_rows": row.get("file_rows"),
                    "usable_pair_rows": row.get("usable_pair_rows"),
                    "live_pair_rows": math.nan,
                    "raw_file_count": math.nan,
                    "raw_subdir_count": math.nan,
                    "raw_payload_status": "",
                    "raw_provider_hints": "",
                    "landing_status_code": "",
                    "landing_final_url": "",
                }
            )

    live = build_live_summary()
    if not live.empty:
        for row in live.to_dict(orient="records"):
            handle = make_source_handle(row.get("project"), row.get("source_dataset"))
            rows.append(
                {
                    "source_handle": handle,
                    "evidence_kind": "live_pair_source",
                    "evidence_key": f"{row.get('project')}|{row.get('source_dataset')}",
                    "project": first_nonempty([row.get("project")]),
                    "source_dataset": first_nonempty([row.get("source_dataset")]),
                    "path": first_nonempty([row.get("raw_file_examples"), str(ALL_PAIRS)]),
                    "terminal_status": "integrated",
                    "promotion_blocker": "",
                    "next_action": "",
                    "notes": "live integrated source summary",
                    "access_class": "",
                    "directness_class": "",
                    "metric_class": "",
                    "integrated_in_build": True,
                    "file_rows": math.nan,
                    "usable_pair_rows": row.get("live_pair_rows"),
                    "live_pair_rows": row.get("live_pair_rows"),
                    "raw_file_count": math.nan,
                    "raw_subdir_count": math.nan,
                    "raw_payload_status": "",
                    "raw_provider_hints": "",
                    "landing_status_code": "",
                    "landing_final_url": "",
                }
            )

    inv = pd.DataFrame(rows)
    if inv.empty:
        return inv
    if "lead_id" not in inv.columns:
        inv["lead_id"] = ""
    inv["lead_id"] = inv.apply(
        lambda r: first_nonempty(
            [
                r.get("lead_id"),
                str(r.get("source_handle", "")).split("lead::", 1)[1] if str(r.get("source_handle", "")).startswith("lead::") else "",
            ]
        ),
        axis=1,
    )
    canonical = inv.apply(assign_canonical_source, axis=1, result_type="expand")
    canonical.columns = ["canonical_source_id", "canonical_source_label", "alias_rule", "alias_confidence"]
    inv = pd.concat([inv, canonical], axis=1)
    inv = inv.sort_values(["source_handle", "evidence_kind", "evidence_key"]).reset_index(drop=True)
    return inv


def summarize_status(group: pd.DataFrame) -> tuple[str, str]:
    kinds = set(group["evidence_kind"])
    integrated = bool_any(group["integrated_in_build"].fillna(False).tolist()) or (
        pd.to_numeric(group["live_pair_rows"], errors="coerce").fillna(0).sum() > 0
    )
    live_rows = int(pd.to_numeric(group["live_pair_rows"], errors="coerce").fillna(0).sum())
    promotion_blocker = first_nonempty(group["promotion_blocker"].tolist())
    terminal_status = first_nonempty(group["terminal_status"].tolist())
    next_action = first_nonempty(group["next_action"].tolist())

    if integrated and live_rows > 0:
        reason = f"included in live build with {live_rows} integrated pair rows"
        if "staged_file" in kinds or "raw_lead_dir" in kinds:
            reason += "; family also retains pre-promotion artifacts"
        if promotion_blocker:
            reason += f"; other artifact notes: {promotion_blocker}"
        return "integrated_live", reason
    if "promoted_file" in kinds:
        reason = "promoted artifact exists"
        if live_rows == 0:
            reason += "; live integration not detected"
        return "promoted_not_live", reason
    if "staged_file" in kinds:
        reason = "staged artifact exists but not promoted"
        if promotion_blocker:
            reason += f"; blocker/status: {promotion_blocker}"
        elif terminal_status:
            reason += f"; terminal_status={terminal_status}"
        return "staged_only", reason
    if "manifest_lead" in kinds or "queue_status" in kinds:
        reason = "lead was logged but no staged/promoted artifact is linked here"
        if terminal_status:
            reason += f"; terminal_status={terminal_status}"
        if promotion_blocker:
            reason += f"; blocker={promotion_blocker}"
        if next_action:
            reason += f"; next_action={next_action}"
        return "logged_attempt_only", reason
    if "raw_lead_dir" in kinds:
        return "raw_artifact_only", "raw lead-harvest directory exists but no structured staged/promoted linkage was found"
    if "source_catalog_row" in kinds:
        integrated_flag = bool_any(group["integrated_in_build"].fillna(False).tolist())
        if integrated_flag:
            return "catalog_integrated", "source catalog marks this source as integrated"
        return "catalog_not_integrated", "source catalog knows this source but it is not integrated in the current build"
    return "unresolved_manual_backfill", "evidence exists but status reconciliation still needs manual backfill"


def choose_display_label(canonical_source_id: str, group: pd.DataFrame) -> str:
    if not is_internal_handle(canonical_source_id):
        preferred_cols = ["canonical_source_label", "source_dataset", "project", "lead_id", "source_handle"]
    else:
        preferred_cols = ["source_dataset", "project", "canonical_source_label", "lead_id", "source_handle"]

    for col in preferred_cols:
        if col not in group.columns:
            continue
        for value in group[col].tolist():
            label = first_nonempty([value])
            if not label or label in {"Multi-project", "nan"}:
                continue
            if is_internal_handle(label):
                continue
            return label

    for col in preferred_cols:
        if col not in group.columns:
            continue
        for value in group[col].tolist():
            label = first_nonempty([value])
            if label and label != "nan":
                return humanize_source_handle(label)
    return humanize_source_handle(canonical_source_id)


def build_audit(inv: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    if inv.empty:
        return pd.DataFrame()

    for canonical_source_id, group in inv.groupby("canonical_source_id", sort=True):
        status, reason = summarize_status(group)
        live_rows = int(pd.to_numeric(group["live_pair_rows"], errors="coerce").fillna(0).sum())
        promoted_paths = sorted({p for p in group.loc[group["evidence_kind"] == "promoted_file", "path"].dropna().astype(str) if p})
        staged_paths = sorted({p for p in group.loc[group["evidence_kind"] == "staged_file", "path"].dropna().astype(str) if p})
        raw_dirs = sorted({p for p in group.loc[group["evidence_kind"] == "raw_lead_dir", "path"].dropna().astype(str) if p})
        lead_ids = sorted({x for x in group["lead_id"].dropna().astype(str) if x and x.lower() != "nan"})
        notes = " | ".join(sorted({n for n in group["notes"].dropna().astype(str) if n}))
        alias_handles = sorted({h for h in group["source_handle"].dropna().astype(str) if h})
        linked_projects = sorted({p for p in group["project"].dropna().astype(str) if p and p.lower() != "nan"})
        linked_datasets = sorted({s for s in group["source_dataset"].dropna().astype(str) if s and s.lower() != "nan"})
        linked_terminal_statuses = sorted({s for s in group["terminal_status"].dropna().astype(str) if s and s.lower() != "nan"})
        alias_rules = sorted({s for s in group["alias_rule"].dropna().astype(str) if s and s != "identity"})
        alias_confidences = sorted({s for s in group["alias_confidence"].dropna().astype(str) if s})
        raw_payload_statuses = sorted({s for s in group.get("raw_payload_status", pd.Series(dtype=str)).dropna().astype(str) if s and s.lower() != "nan"})
        raw_provider_hints = sorted({s for s in group.get("raw_provider_hints", pd.Series(dtype=str)).dropna().astype(str) if s and s.lower() != "nan"})
        landing_status_codes = sorted({s for s in group.get("landing_status_code", pd.Series(dtype=str)).dropna().astype(str) if s and s.lower() != "nan"})
        landing_urls = sorted({s for s in group.get("landing_final_url", pd.Series(dtype=str)).dropna().astype(str) if s and s.lower() != "nan"})
        raw_file_count = int(pd.to_numeric(group.get("raw_file_count", pd.Series(dtype=float)), errors="coerce").fillna(0).sum())
        raw_subdir_count = int(pd.to_numeric(group.get("raw_subdir_count", pd.Series(dtype=float)), errors="coerce").fillna(0).sum())
        blocker_codes = sorted(
            {
                code
                for text in (
                    list(group["promotion_blocker"].dropna().astype(str))
                    + list(group["notes"].dropna().astype(str))
                    + list(group["terminal_status"].dropna().astype(str))
                    + raw_payload_statuses
                )
                for code in normalize_blocker_codes(text)
            }
        )
        catalog_role_codes = sorted(
            {
                code
                for text in (
                    list(group["notes"].dropna().astype(str))
                    + list(group["directness_class"].dropna().astype(str))
                    + list(group["promotion_blocker"].dropna().astype(str))
                )
                for code in normalize_catalog_role_codes(text)
            }
        )
        if status == "integrated_live":
            included_reason_code = "integrated_live_pairs"
            excluded_reason_code = ""
        elif status == "catalog_integrated":
            included_reason_code = "catalog_integrated_supporting_source"
            excluded_reason_code = ""
        else:
            included_reason_code = ""
            excluded_reason_code = {
                "staged_only": "staged_not_promoted",
                "promoted_not_live": "promoted_not_integrated",
                "logged_attempt_only": "logged_attempt_only",
                "raw_artifact_only": "raw_artifact_only",
                "catalog_not_integrated": "catalog_known_not_integrated",
                "unresolved_manual_backfill": "manual_backfill_required",
            }.get(status, "manual_backfill_required")
        rows.append(
            {
                "canonical_source_id": canonical_source_id,
                "canonical_source_label": choose_display_label(str(canonical_source_id), group),
                "source_handle": canonical_source_id,
                "audit_status": status,
                "included_reason_code": included_reason_code,
                "excluded_reason_code": excluded_reason_code,
                "blocker_codes": " | ".join(blocker_codes),
                "has_blocked_artifacts": bool(blocker_codes),
                "catalog_role_codes": " | ".join(catalog_role_codes),
                "status_explanation": reason,
                "project": first_nonempty(linked_projects),
                "source_dataset": first_nonempty(linked_datasets),
                "lead_id": " | ".join(lead_ids),
                "linked_projects": " | ".join(linked_projects),
                "linked_source_datasets": " | ".join(linked_datasets),
                "linked_terminal_statuses": " | ".join(linked_terminal_statuses),
                "alias_handles": " | ".join(alias_handles),
                "alias_count": len(alias_handles),
                "alias_rule": " | ".join(alias_rules),
                "alias_confidence": first_nonempty(alias_confidences),
                "raw_file_count": raw_file_count,
                "raw_subdir_count": raw_subdir_count,
                "raw_payload_statuses": " | ".join(raw_payload_statuses),
                "raw_provider_hints": " | ".join(raw_provider_hints),
                "landing_status_codes": " | ".join(landing_status_codes),
                "landing_final_urls": " | ".join(landing_urls[:5]),
                "evidence_surfaces": "; ".join(sorted(group["evidence_kind"].unique())),
                "manifest_logged": "manifest_lead" in set(group["evidence_kind"]),
                "queue_logged": "queue_status" in set(group["evidence_kind"]),
                "raw_dir_present": "raw_lead_dir" in set(group["evidence_kind"]),
                "staged_present": "staged_file" in set(group["evidence_kind"]),
                "promoted_present": "promoted_file" in set(group["evidence_kind"]),
                "catalog_present": "source_catalog_row" in set(group["evidence_kind"]),
                "integrated_in_build": bool_any(group["integrated_in_build"].fillna(False).tolist()) or live_rows > 0,
                "live_pair_rows": live_rows,
                "catalog_file_rows": int(pd.to_numeric(group["file_rows"], errors="coerce").fillna(0).max()) if pd.to_numeric(group["file_rows"], errors="coerce").fillna(0).max() > 0 else 0,
                "catalog_usable_pair_rows": int(pd.to_numeric(group["usable_pair_rows"], errors="coerce").fillna(0).max()) if pd.to_numeric(group["usable_pair_rows"], errors="coerce").fillna(0).max() > 0 else 0,
                "terminal_status": first_nonempty(group["terminal_status"].tolist()),
                "promotion_blocker": first_nonempty(group["promotion_blocker"].tolist()),
                "next_action": first_nonempty(group["next_action"].tolist()),
                "staged_paths": " | ".join(staged_paths),
                "promoted_paths": " | ".join(promoted_paths),
                "raw_dirs": " | ".join(raw_dirs),
                "notes": notes,
                "needs_manual_backfill": (
                    status in {"unresolved_manual_backfill", "raw_artifact_only", "logged_attempt_only", "staged_only"}
                    or (status == "catalog_not_integrated" and not catalog_role_codes)
                    or bool(
                        {
                            "roster_only",
                            "pilot_effect_missing",
                            "pilot_n_and_variance_missing",
                            "needs_primary_pdf_confirmation",
                            "access_restriction",
                        }
                        & set(blocker_codes)
                    )
                ),
            }
        )

    audit = pd.DataFrame(rows).sort_values(
        ["audit_status", "canonical_source_label", "project", "source_dataset", "canonical_source_id"]
    ).reset_index(drop=True)
    return audit


def derive_worklist(audit: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    if audit.empty:
        return pd.DataFrame()

    for row in audit.to_dict(orient="records"):
        status = str(row.get("audit_status", ""))
        blocker_codes = {x.strip() for x in str(row.get("blocker_codes", "")).split("|") if x.strip()}
        catalog_role_codes = {x.strip() for x in str(row.get("catalog_role_codes", "")).split("|") if x.strip()}
        raw_statuses = {x.strip() for x in str(row.get("raw_payload_statuses", "")).split("|") if x.strip()}
        live_rows = int(row.get("live_pair_rows", 0) or 0)

        priority = 0
        next_step = "none"
        rationale = ""

        if status == "staged_only" and "downloaded_payload_present" in raw_statuses and "parser_not_implemented" in blocker_codes:
            priority = 100
            next_step = "implement_parser_and_promote"
            rationale = "Downloaded payloads already exist and the main blocker is parser work."
        elif status == "staged_only" and "downloaded_payload_present" in raw_statuses and "conversion_policy_missing" in blocker_codes:
            priority = 95
            next_step = "define_metric_conversion_policy"
            rationale = "Downloaded payloads exist; promotion is blocked mostly by unresolved conversion logic."
        elif status == "raw_artifact_only" and "downloaded_payload_present" in raw_statuses:
            priority = 90
            next_step = "stage_downloaded_payload"
            rationale = "Public files appear downloaded but have not been staged into a structured source artifact."
        elif status == "integrated_live" and row.get("needs_manual_backfill"):
            priority = 85
            next_step = "complete_partial_manual_reconstruction"
            rationale = "Source family is already live but still has unresolved manual reconstruction work."
        elif status == "staged_only" and "access_restriction" in blocker_codes:
            priority = 45
            next_step = "resolve_access_block"
            rationale = "The source appears relevant but the needed payload is restricted or failed with an access error."
        elif status == "staged_only" and "source_not_pair_buildable" in blocker_codes:
            priority = 0
        elif status == "staged_only" and "missing_machine_readable_pair_results" in blocker_codes:
            priority = 55
            next_step = "locate_machine_readable_payload"
            rationale = "The checked public materials do not currently expose a machine-readable pair-results payload."
        elif status == "staged_only" and "metric_not_on_shared_d_axis" in blocker_codes:
            priority = 70
            next_step = "consider_native_metric_lane"
            rationale = "Source is real but blocked by the current shared-D policy."
        elif status == "staged_only" and "original_side_missing" in blocker_codes:
            priority = 65
            next_step = "recover_original_side_or_native_metric_lane"
            rationale = "Source is real but the current local files do not expose a complete original-versus-replication D/N pair."
        elif status == "raw_artifact_only" and "landing_probe_only" in raw_statuses:
            priority = 50
            next_step = "download_public_payload"
            rationale = "Only the landing page was probed; no file payload has been staged."
        elif status == "raw_artifact_only" and "landing_probe_blocked" in raw_statuses:
            priority = 45
            next_step = "resolve_access_block"
            rationale = "Lead is known but current acquisition stopped at an access block."
        elif status == "catalog_not_integrated" and (
            "cross_check_only" in blocker_codes or "catalog_cross_check_only" in catalog_role_codes
        ):
            priority = 0
        elif status == "catalog_not_integrated":
            priority = 40
            next_step = "review_catalog_source_for_integration"
            rationale = "Catalog knows the source but integration rationale is still thin."

        if priority > 0:
            rows.append(
                {
                    "canonical_source_id": row.get("canonical_source_id"),
                    "canonical_source_label": row.get("canonical_source_label"),
                    "audit_status": status,
                    "live_pair_rows": live_rows,
                    "blocker_codes": row.get("blocker_codes", ""),
                    "raw_payload_statuses": row.get("raw_payload_statuses", ""),
                    "linked_projects": row.get("linked_projects", ""),
                    "linked_source_datasets": row.get("linked_source_datasets", ""),
                    "worklist_priority": priority,
                    "recommended_next_step": next_step,
                    "worklist_rationale": rationale,
                    "staged_paths": row.get("staged_paths", ""),
                    "promoted_paths": row.get("promoted_paths", ""),
                    "raw_dirs": row.get("raw_dirs", ""),
                }
            )

    worklist = pd.DataFrame(rows)
    if worklist.empty:
        return worklist
    return worklist.sort_values(
        ["worklist_priority", "audit_status", "canonical_source_label"],
        ascending=[False, True, True],
    ).reset_index(drop=True)


def write_markdown(audit: pd.DataFrame, inventory: pd.DataFrame) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    status_counts = audit["audit_status"].value_counts().sort_index()
    evidence_counts = inventory["evidence_kind"].value_counts().sort_index()
    blocker_counts = (
        audit["blocker_codes"]
        .fillna("")
        .astype(str)
        .str.split(r"\s+\|\s+")
        .explode()
        .loc[lambda s: s.astype(str).str.strip() != ""]
        .value_counts()
        .sort_index()
    )
    raw_payload_counts = (
        audit["raw_payload_statuses"]
        .fillna("")
        .astype(str)
        .str.split(r"\s+\|\s+")
        .explode()
        .loc[lambda s: s.astype(str).str.strip() != ""]
        .value_counts()
        .sort_index()
    )

    worklist = derive_worklist(audit)

    lines = [
        "# Replication Source Audit",
        "",
        "This report is a reconciliation pass across every current tracking surface, not just the harvest manifest.",
        "The evidence inventory is intentionally non-lossy. The consolidated audit is alias-reconciled at the source-family level.",
        "",
        f"- Audit rows: **{len(audit):,}**",
        f"- Evidence inventory rows: **{len(inventory):,}**",
        "",
        "## Audit status counts",
        "",
        "| Audit status | Rows |",
        "|---|---:|",
    ]
    for idx, val in status_counts.items():
        lines.append(f"| {idx} | {int(val)} |")

    lines += [
        "",
        "## Evidence surface counts",
        "",
        "| Evidence kind | Rows |",
        "|---|---:|",
    ]
    for idx, val in evidence_counts.items():
        lines.append(f"| {idx} | {int(val)} |")

    lines += [
        "",
        "## Normalized blocker codes",
        "",
        "| Blocker code | Rows |",
        "|---|---:|",
    ]
    for idx, val in blocker_counts.items():
        lines.append(f"| {idx} | {int(val)} |")

    lines += [
        "",
        "## Raw payload status codes",
        "",
        "| Raw payload status | Rows |",
        "|---|---:|",
    ]
    for idx, val in raw_payload_counts.items():
        lines.append(f"| {idx} | {int(val)} |")

    lines += [
        "",
        "## Reconciled source families with blockers",
        "",
        "| Canonical source | Audit status | Blocker codes | Linked datasets | Status explanation |",
        "|---|---|---|---|---|",
    ]
    manual = audit.loc[audit["needs_manual_backfill"] | (audit["blocker_codes"].fillna("") != "")].copy()
    for row in manual.head(120).itertuples(index=False):
        lines.append(
            f"| {row.canonical_source_label} | {row.audit_status} | {row.blocker_codes} | {row.linked_source_datasets} | {row.status_explanation} |"
        )

    lines += [
        "",
        "## Raw-only leads",
        "",
        "| Canonical source | Raw payload status | Landing status codes | Raw provider hints | Status explanation |",
        "|---|---|---|---|---|",
    ]
    raw_only = audit.loc[audit["audit_status"] == "raw_artifact_only"].copy()
    for row in raw_only.itertuples(index=False):
        lines.append(
            f"| {row.canonical_source_label} | {row.raw_payload_statuses} | {row.landing_status_codes} | {row.raw_provider_hints} | {row.status_explanation} |"
        )

    lines += [
        "",
        "## Top worklist items",
        "",
        "| Priority | Canonical source | Next step | Rationale |",
        "|---:|---|---|---|",
    ]
    for row in worklist.head(30).itertuples(index=False):
        lines.append(
            f"| {row.worklist_priority} | {row.canonical_source_label} | {row.recommended_next_step} | {row.worklist_rationale} |"
        )

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    inventory = build_inventory()
    audit = build_audit(inventory)
    worklist = derive_worklist(audit)

    DERIVED.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    inventory.to_csv(OUT_INVENTORY, index=False)
    audit.to_csv(OUT_AUDIT, index=False)
    worklist.to_csv(OUT_WORKLIST, index=False)
    write_markdown(audit, inventory)

    print(f"Wrote evidence inventory: {OUT_INVENTORY}")
    print(f"Wrote source audit: {OUT_AUDIT}")
    print(f"Wrote source worklist: {OUT_WORKLIST}")
    print(f"Wrote audit report: {OUT_MD}")
    print(f"Audit rows: {len(audit)}; inventory rows: {len(inventory)}; worklist rows: {len(worklist)}")


if __name__ == "__main__":
    main()
