#!/usr/bin/env python3
"""Build a GPT handoff packet for unresolved individual-replication leads.

The automatic mining pass promotes rows only when source text already supports
both D/N values. This script packages the remaining value-bearing blockers into
a compact TSV plus a prompt that can be sent to GPT or another researcher.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
WORKLIST_DIR = ROOT / "steps" / "individual_replication_papers" / "figure1"
AUTO_DIR = WORKLIST_DIR / "auto_mining"

VALUE_SCAN = WORKLIST_DIR / "individual-paper-value-scan-batch001.tsv"
MANUAL_TASK = WORKLIST_DIR / "individual-paper-manual-acquisition-task-batch007.tsv"
AUTO_ATTEMPTS = AUTO_DIR / "individual-paper-auto-acquisition-attempts.tsv"
EMBEDDED_PDFS = AUTO_DIR / "individual-paper-embedded-pdf-downloads.tsv"
PROMOTED = (
    ROOT
    / "data"
    / "derived"
    / "replication_pairs"
    / "harvest"
    / "promoted"
    / "individual_replication_papers__promoted_pairs.csv"
)
FIGURE1 = ROOT / "FIGURE1_REPLICATION_PAIRS.tsv"

OUT_TSV = AUTO_DIR / "individual-paper-gpt-handoff-after-auto-mining.tsv"
OUT_MD = ROOT / "reports" / "figure1_individual_replication_gpt_handoff_after_auto_mining_2026-05-05.md"

RAW_BATCH_DIRS = [
    ROOT / "data" / "raw" / "replication_projects" / "individual_search_batch001",
    ROOT / "data" / "raw" / "replication_projects" / "individual_search_batch002",
    ROOT / "data" / "raw" / "replication_projects" / "individual_search_batch003",
    ROOT / "data" / "raw" / "replication_projects" / "individual_search_batch004",
    ROOT / "data" / "raw" / "replication_projects" / "individual_search_batch006",
    ROOT / "data" / "raw" / "replication_projects" / "individual_auto_mining_blockers",
]

BLOCKER_PATTERN = re.compile(
    "|".join(
        [
            "source_blocked",
            "needs_event",
            "manual_acquisition",
            "original_effect",
            "original_n",
            "replication_n_not_larger_or_original_effect_missing",
            "conceptual_changed_task_original_effect_missing",
            "conceptual_extension_no_single_original_effect",
        ]
    )
)

PRIORITY_OVERRIDES = {
    "api_candidate_c49eb133d5977b06": 1,
    "api_candidate_821f217890822e88": 1,
    "api_candidate_64a39a53876c51c1": 1,
    "api_candidate_006071e798115bf1": 1,
    "api_candidate_a939357d526cdfa3": 1,
    "api_candidate_710fd7eb55fc9d77": 1,
    "api_candidate_0eb40892da116803": 1,
    "api_candidate_96a758378eb37b0e": 2,
    "api_candidate_d98523e0ce3e5e0d": 2,
    "api_candidate_0367fa32a3d09f7b": 2,
    "IND-017": 2,
    "IND-022": 2,
    "IND-023": 2,
    "IND-024": 2,
}


OUT_COLUMNS = [
    "handoff_id",
    "candidate_id",
    "priority",
    "candidate_name",
    "candidate_route",
    "scan_decision",
    "blocker",
    "original_title",
    "original_doi",
    "replication_title",
    "replication_doi",
    "source_object_urls",
    "local_file_summary",
    "known_original_support_text",
    "known_replication_support_text",
    "conversion_or_policy_note",
    "gpt_task",
    "expected_json_decision_values",
]


def clean(value: Any, max_len: int = 20000) -> str:
    if value is None:
        return ""
    text = str(value).replace("\t", " ").replace("\r", " ").replace("\n", " ").strip()
    text = re.sub(r"\s+", " ", text)
    return text[:max_len]


def read_tsv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False).fillna("")


def read_any_table(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    sep = "," if path.suffix == ".csv" else "\t"
    return pd.read_csv(path, sep=sep, dtype=str, keep_default_na=False).fillna("")


def relpath(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def split_field(value: Any) -> list[str]:
    text = clean(value)
    if not text:
        return []
    return [part.strip() for part in re.split(r"\s+\|\s+|\s*;\s*", text) if part.strip()]


def stable_id(prefix: str, *parts: Any) -> str:
    payload = "||".join(clean(part, max_len=5000) for part in parts)
    digest = hashlib.sha1(payload.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"


def parse_json_list(value: str) -> list[str]:
    text = clean(value, max_len=100000)
    if not text:
        return []
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return [text]
    if isinstance(payload, list):
        return [clean(item) for item in payload if clean(item)]
    return [clean(payload)]


def first_nonempty(*values: Any) -> str:
    for value in values:
        text = clean(value)
        if text:
            return text
    return ""


def path_kind(path: Path) -> str:
    suffix = path.suffix.lower().lstrip(".") or "file"
    try:
        with path.open("rb") as handle:
            start = handle.read(16)
    except OSError:
        return suffix
    if start.startswith(b"%PDF"):
        return "pdf"
    if start.lstrip().startswith((b"<html", b"<!DOCTYPE", b"<?xml")):
        return "html_or_xml"
    if start.lstrip().startswith((b"{", b"[")):
        return "json_like"
    return suffix


def file_summary(paths: list[str], max_paths: int = 14) -> str:
    rows: list[str] = []
    seen: set[str] = set()
    for path_text in paths:
        if not path_text or path_text in seen:
            continue
        seen.add(path_text)
        path = Path(path_text)
        abs_path = path if path.is_absolute() else ROOT / path
        if not abs_path.exists():
            rows.append(f"{path_text} [missing]")
            continue
        rows.append(f"{relpath(abs_path)} [{path_kind(abs_path)}, {abs_path.stat().st_size} bytes]")
        if len(rows) >= max_paths:
            remaining = len([p for p in paths if p not in seen])
            if remaining > 0:
                rows.append(f"... {remaining} more local files omitted from prompt row")
            break
    return " | ".join(rows)


def candidate_files(candidate_id: str) -> list[str]:
    paths: list[str] = []
    for raw_dir in RAW_BATCH_DIRS:
        candidate_dir = raw_dir / candidate_id
        if not candidate_dir.exists():
            continue
        for path in sorted(candidate_dir.rglob("*")):
            if path.is_file():
                paths.append(relpath(path))
    return paths


def local_paths_for(candidate_id: str, row: pd.Series, manual_row: dict[str, str], attempts: pd.DataFrame, embedded: pd.DataFrame) -> list[str]:
    paths: list[str] = []
    paths.extend(split_field(row.get("local_support_paths")))
    paths.extend(split_field(manual_row.get("local_support_paths")))
    if not attempts.empty and "candidate_id" in attempts.columns:
        subset = attempts[attempts["candidate_id"].eq(candidate_id)]
        paths.extend([clean(value) for value in subset.get("local_path", pd.Series(dtype=str)).tolist() if clean(value)])
    if not embedded.empty and "candidate_id" in embedded.columns:
        subset = embedded[embedded["candidate_id"].eq(candidate_id)]
        paths.extend([clean(value) for value in subset.get("local_path", pd.Series(dtype=str)).tolist() if clean(value)])
    paths.extend(candidate_files(candidate_id))
    deduped: list[str] = []
    for path in paths:
        if path and path not in deduped:
            deduped.append(path)
    return deduped


def source_urls_for(row: pd.Series, manual_row: dict[str, str]) -> list[str]:
    urls: list[str] = []
    urls.extend(parse_json_list(manual_row.get("source_object_urls_json", "")))
    for field in ["source_object_urls_json", "source_urls", "url"]:
        if field in row.index:
            urls.extend(parse_json_list(row.get(field, "")))
    deduped: list[str] = []
    for url in urls:
        if url and url not in deduped:
            deduped.append(url)
    return deduped


def priority_for(candidate_id: str, decision: str) -> int:
    if candidate_id in PRIORITY_OVERRIDES:
        return PRIORITY_OVERRIDES[candidate_id]
    if "needs_event" in decision or "manual_acquisition" in decision:
        return 2
    if "source_blocked" in decision:
        return 2
    if "original_effect" in decision or "original_n" in decision:
        return 2
    return 3


def task_for(candidate_id: str, decision: str, next_action: str) -> str:
    specific = {
        "api_candidate_c49eb133d5977b06": "Resolve Rabbitt (1968) Experiment 2 original analyzed N and confirm the exact target-description outcome that maps to the open preregistered weapon-focus replication.",
        "api_candidate_821f217890822e88": "Decide whether the Mehta/Zhu anagram color-priming interaction can be converted to a defensible Figure 1 D row; if yes, return exact original and replication effect/N with formula.",
        "api_candidate_64a39a53876c51c1": "Resolve Pickel and Sneyd (2018) Experiment 2 original N/effect and map it to the replication's target-description or lineup outcome.",
        "api_candidate_006071e798115bf1": "Extract Shenhav/Rand/Greene original two-condition effect and N for the intuitive-mindset belief-in-God target, then map to the replication t/N.",
        "api_candidate_a939357d526cdfa3": "Find article/supplement/data for the Collabra Griskevicius status-motivation replication and determine the primary pro-environmental-choice D/N row, not only the manipulation-check abstract values.",
        "api_candidate_710fd7eb55fc9d77": "Acquire the original scopolamine antidepressant article or authoritative table and determine the matched crossover D/N route for the replication.",
        "api_candidate_0eb40892da116803": "Acquire the Cognition approximate-arithmetic replication and original Park/Brannon target source; extract matched symbolic arithmetic fluency effect/N.",
        "api_candidate_96a758378eb37b0e": "Determine whether the phonological-priming rapid-naming paper is a valid close/direct row or should be rejected because the task differs from Hillinger's lexical-decision original.",
        "api_candidate_d98523e0ce3e5e0d": "Extract exact Shen online-image-credibility original and direct-replication effect/N values or classify as native-only/coverage-only.",
        "api_candidate_0367fa32a3d09f7b": "Acquire the Loftus misinformation registered-report replication and extract matched original/replication effect/N if publicly available.",
    }
    if candidate_id in specific:
        return specific[candidate_id]
    if next_action:
        return next_action
    return "Resolve source objects, extract original and replication D/N or return a reject/native-only decision with evidence."


def build_rows() -> pd.DataFrame:
    scan = read_tsv(VALUE_SCAN)
    manual = read_tsv(MANUAL_TASK)
    attempts = read_tsv(AUTO_ATTEMPTS)
    embedded = read_tsv(EMBEDDED_PDFS)
    if scan.empty:
        raise FileNotFoundError(f"Missing value scan: {VALUE_SCAN}")

    manual_by_candidate = (
        manual.drop_duplicates("candidate_id", keep="last").set_index("candidate_id", drop=False).to_dict(orient="index")
        if not manual.empty and "candidate_id" in manual.columns
        else {}
    )

    rows: list[dict[str, Any]] = []
    for _, scan_row in scan.iterrows():
        decision = clean(scan_row.get("scan_decision"))
        if decision == "ready_for_source_result_build":
            continue
        if not BLOCKER_PATTERN.search(decision):
            continue
        candidate_id = clean(scan_row.get("candidate_id"))
        manual_row = manual_by_candidate.get(candidate_id, {})
        paths = local_paths_for(candidate_id, scan_row, manual_row, attempts, embedded)
        urls = source_urls_for(scan_row, manual_row)
        original_title = first_nonempty(scan_row.get("original_title_override"), manual_row.get("original_title"))
        replication_title = first_nonempty(scan_row.get("replication_title_override"), manual_row.get("replication_title"))
        candidate_name = first_nonempty(manual_row.get("candidate_name"), scan_row.get("result_option_label"))
        next_action = clean(scan_row.get("next_action")) or clean(manual_row.get("needed_evidence"))
        rows.append(
            {
                "handoff_id": stable_id("gpt_handoff", candidate_id, scan_row.get("result_option_label"), decision),
                "candidate_id": candidate_id,
                "priority": str(priority_for(candidate_id, decision)),
                "candidate_name": candidate_name,
                "candidate_route": first_nonempty(scan_row.get("candidate_route"), manual_row.get("candidate_route")),
                "scan_decision": decision,
                "blocker": first_nonempty(manual_row.get("blocker_category"), decision),
                "original_title": original_title,
                "original_doi": first_nonempty(scan_row.get("original_doi_override"), manual_row.get("original_doi")),
                "replication_title": replication_title,
                "replication_doi": first_nonempty(scan_row.get("replication_doi_override"), manual_row.get("replication_doi")),
                "source_object_urls": " | ".join(urls),
                "local_file_summary": file_summary(paths),
                "known_original_support_text": clean(scan_row.get("original_support_text"), max_len=5000),
                "known_replication_support_text": clean(scan_row.get("replication_support_text"), max_len=5000),
                "conversion_or_policy_note": first_nonempty(scan_row.get("conversion_or_policy_note"), manual_row.get("conversion_or_policy_note")),
                "gpt_task": task_for(candidate_id, decision, next_action),
                "expected_json_decision_values": "ready_for_row | needs_more_evidence | native_only | reject",
            }
        )
    df = pd.DataFrame(rows, columns=OUT_COLUMNS).fillna("")
    if not df.empty:
        df["priority_int"] = df["priority"].astype(int)
        df = df.sort_values(["priority_int", "candidate_id", "handoff_id"]).drop(columns=["priority_int"])
    return df


def table_count(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open(encoding="utf-8", errors="replace") as handle:
        return max(sum(1 for _ in handle) - 1, 0)


def write_prompt(df: pd.DataFrame) -> None:
    figure_rows = table_count(FIGURE1)
    promoted_rows = table_count(PROMOTED)
    priority_counts = df["priority"].value_counts().sort_index().to_dict() if not df.empty else {}
    lines = [
        "# GPT Handoff: Individual Replication Papers After Automatic Mining",
        "",
        "We are building Figure 1 rows at the paper-pair/study-outcome level. Automatic local mining has already promoted every row it could support from mirrored value-bearing source text. The remaining rows below need outside search, exact source-object acquisition, or judgment about whether the design/outcome can be mapped to Figure 1.",
        "",
        "Current local counts:",
        f"- Figure 1 plotted table rows: {figure_rows:,}",
        f"- Promoted individual-replication rows: {promoted_rows:,}",
        f"- Handoff candidates in this packet: {len(df):,}",
        f"- Priority distribution: {priority_counts}",
        "",
        "Important rules:",
        "- Do not infer values from vibes or from a citation alone.",
        "- A usable Figure 1 row needs a specific original result mapped to a specific replication/follow-up result, original N, replication N, original effect, replication effect, and a defensible D/SMD or D-equivalent conversion route.",
        "- If the source only supports a native regression, interaction, survival, genetics, psychometric, or one-arm result, return `native_only` unless a concrete conversion is justified.",
        "- If a source object is blocked or the exact original/replication outcome is ambiguous, return `needs_more_evidence` with the next source to acquire.",
        "- Preserve verbatim source text for effect, N, relationship, outcome selector, and conversion inputs.",
        "",
        "Return strict JSON with this shape:",
        "",
        "```json",
        "[",
        "  {",
        '    "candidate_id": "api_candidate_...",',
        '    "decision": "ready_for_row|needs_more_evidence|native_only|reject",',
        '    "replication_kind": "direct_replication|close_replication|clinical_followup|independent_validation|other",',
        '    "row_policy": "strict_figure1a|d_equivalent_figure1b|native_only|coverage_only|reject",',
        '    "original": {',
        '      "title": "", "authors_year": "", "doi": "", "pmid": "", "pmcid": "",',
        '      "study_or_experiment": "", "outcome": "", "contrast": "",',
        '      "n": "", "effect": "", "effect_metric": "",',
        '      "verbatim_effect_text": "", "verbatim_n_text": "",',
        '      "source_url": "", "locator": ""',
        "    },",
        '    "replication": {',
        '      "title": "", "authors_year": "", "doi": "", "pmid": "", "pmcid": "",',
        '      "study_or_experiment": "", "outcome": "", "contrast": "",',
        '      "n": "", "effect": "", "effect_metric": "",',
        '      "verbatim_effect_text": "", "verbatim_n_text": "",',
        '      "source_url": "", "locator": ""',
        "    },",
        '    "relationship_evidence": {',
        '      "verbatim_text": "", "source_url": "", "locator": ""',
        "    },",
        '    "conversion": {',
        '      "route": "native_d|means_sds_to_d|t_to_d|f_to_d|r_to_d|event_counts_to_logor_to_d|native_only|none",',
        '      "formula": "", "computed_original_d": null, "computed_replication_d": null,',
        '      "assumptions": []',
        "    },",
        '    "source_objects_to_mirror": [],',
        '    "blockers": [],',
        '    "notes": ""',
        "  }",
        "]",
        "```",
        "",
        f"Machine-readable queue: `{OUT_TSV.relative_to(ROOT)}`",
        "",
        "## Priority Candidates",
        "",
    ]
    for _, row in df.iterrows():
        lines.extend(
            [
                f"### Priority {row['priority']} - {row['candidate_id']}",
                "",
                f"- Candidate: {row['candidate_name']}",
                f"- Route/decision: `{row['candidate_route']}` / `{row['scan_decision']}`",
                f"- Original: {row['original_title']} ({row['original_doi']})",
                f"- Replication: {row['replication_title']} ({row['replication_doi']})",
                f"- Source URLs: {row['source_object_urls'] or 'none recorded'}",
                f"- Local files already mirrored: {row['local_file_summary'] or 'none'}",
                f"- Known original support: {row['known_original_support_text'] or 'none'}",
                f"- Known replication support: {row['known_replication_support_text'] or 'none'}",
                f"- Conversion/policy note: {row['conversion_or_policy_note'] or 'none'}",
                f"- Task: {row['gpt_task']}",
                "",
            ]
        )
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    AUTO_DIR.mkdir(parents=True, exist_ok=True)
    OUT_TSV.parent.mkdir(parents=True, exist_ok=True)
    df = build_rows()
    df.to_csv(OUT_TSV, sep="\t", index=False)
    write_prompt(df)
    print(f"Wrote {len(df)} handoff rows to {OUT_TSV.relative_to(ROOT)}")
    print(f"Wrote prompt to {OUT_MD.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
