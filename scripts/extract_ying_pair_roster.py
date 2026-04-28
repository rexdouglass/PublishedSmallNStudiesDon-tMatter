#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TSV_PATH = ROOT / "data/raw/replication_projects/ying_2023/YING-DISSERTATION-2023.tsv"
OUT_DIR = ROOT / "data/derived/replication_pairs/harvest/staged"
OUT_CSV = OUT_DIR / "ying_2023_pair_roster__stage.csv"

START_PAGE = 94
END_PAGE = 138
MIDPOINT = 300.0
PAGE_SPAN = 1000.0

PAIR_RE = re.compile(r"^\s*(\d{1,3})\s+((?:[A-Z]|de\b|das\b|van\b|von\b|del\b|da\b).*)$")
DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", flags=re.IGNORECASE)


def normalize_spaces(text: str) -> str:
    text = text.replace("‐", "-").replace("–", "-").replace("—", "-").replace("", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def canonical_top(value: float) -> float:
    return round(float(value), 1)


def build_side_lines(tsv: pd.DataFrame, side: str) -> list[tuple[float, float, int, str]]:
    if side == "left":
        words = tsv[(tsv["level"] == 5) & (tsv["page_num"].between(START_PAGE, END_PAGE)) & (tsv["left"] < MIDPOINT)].copy()
    else:
        words = tsv[(tsv["level"] == 5) & (tsv["page_num"].between(START_PAGE, END_PAGE)) & (tsv["left"] >= MIDPOINT)].copy()
    words["text"] = words["text"].astype(str)
    words["top_key"] = words["top"].map(canonical_top)

    lines: list[tuple[float, float, int, str]] = []
    grouped = words.groupby(["page_num", "top_key"], sort=True)
    for (page_num, top_key), g in grouped:
        text = " ".join(g.sort_values("left")["text"].tolist())
        text = normalize_spaces(text)
        if not text:
            continue
        if text.startswith("eTable 3."):
            continue
        if side == "left" and text in {"Pair Pilot trial", "#", "84", "85", "86", "87", "88", "89", "90", "91", "92", "93", "94", "95", "96", "97", "98", "99", "100", "101", "102", "103", "104", "105", "106", "107", "108", "109", "110", "111", "112", "113", "114", "115", "116", "117", "118", "119", "120", "121", "122", "123", "124", "125", "126", "127", "128"}:
            continue
        if side == "right" and text == "Full-scale trial":
            continue
        global_top = page_num * PAGE_SPAN + top_key
        lines.append((global_top, top_key, int(page_num), text))
    lines.sort(key=lambda x: x[0])
    return lines


def extract_pairs(left_lines: list[tuple[float, float, int, str]], right_lines: list[tuple[float, float, int, str]]) -> list[dict[str, object]]:
    starts: list[tuple[int, float, float, int, str]] = []
    for i, (global_top, top_key, page_num, text) in enumerate(left_lines):
        m = PAIR_RE.match(text)
        if m:
            starts.append((int(m.group(1)), global_top, top_key, page_num, m.group(2).strip()))

    pairs: list[dict[str, object]] = []
    for idx, (pair_num, start_global, start_top_key, start_page, pilot_start_text) in enumerate(starts):
        end_global = starts[idx + 1][1] if idx + 1 < len(starts) else float("inf")
        left_segment = [text for global_top, _, _, text in left_lines if start_global <= global_top < end_global]
        right_segment = [text for global_top, _, _, text in right_lines if start_global <= global_top < end_global]

        if left_segment:
            first = left_segment[0]
            m = PAIR_RE.match(first)
            if m:
                left_segment[0] = m.group(2).strip()

        pilot_text = normalize_spaces(" ".join(left_segment))
        full_text = normalize_spaces(" ".join(right_segment))
        pairs.append(
            {
                "pair_number": pair_num,
                "pilot_citation_text": pilot_text,
                "full_scale_citation_text": full_text,
                "start_page_num": start_page,
            }
        )
    return pairs


def clean_doi(text: str) -> str:
    text = text.replace(" ", "")
    m = DOI_RE.search(text)
    return m.group(0).rstrip(".,;)") if m else ""


def main() -> None:
    tsv = pd.read_csv(TSV_PATH, sep="\t")
    left_lines = build_side_lines(tsv, "left")
    right_lines = build_side_lines(tsv, "right")
    pairs = extract_pairs(left_lines, right_lines)

    rows = []
    for pair in pairs:
        rows.append(
            {
                "source_dataset": "ying_2023_dissertation_pair_roster",
                "source_paper": "Ying 2023 dissertation Appendix A eTable 3",
                "pair_id": f"ying_2023__pair_{int(pair['pair_number']):03d}",
                "pair_number": int(pair["pair_number"]),
                "pilot_citation_text": pair["pilot_citation_text"],
                "pilot_doi": clean_doi(pair["pilot_citation_text"]),
                "full_scale_citation_text": pair["full_scale_citation_text"],
                "full_scale_doi": clean_doi(pair["full_scale_citation_text"]),
                "start_page_num": int(pair["start_page_num"]),
                "stage_status": "roster_only",
                "analytic_row_status": "effect_sizes_and_ns_not_exposed_in_roster",
                "public_source_path": str(ROOT / "data/raw/YING-DISSERTATION-2023.pdf"),
            }
        )

    df = pd.DataFrame(rows).sort_values("pair_number").reset_index(drop=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_CSV, index=False)
    print(f"wrote {len(df)} rows to {OUT_CSV}")
    print(df.head(3).to_string(index=False))


if __name__ == "__main__":
    main()
