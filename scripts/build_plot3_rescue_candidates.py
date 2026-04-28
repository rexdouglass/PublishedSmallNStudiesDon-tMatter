#!/usr/bin/env python3
"""Build conservative Plot 3 rescue-candidate queues from local public-source pulls.

These outputs are deliberately *not* appended to strict Plot 3.  They turn the
large crash-note sources into auditable work queues with candidate D/N values
and a promotion status that records the remaining blocker.
"""

from __future__ import annotations

import math
import re
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = ROOT / "data" / "derived" / "effect_inflation_dataset"

SCHEEL_TSV = ROOT / "data" / "raw" / "corpus_candidates" / "scheel_2021" / "positive_results_in_registered_reports_data.tsv"
VDA_RAW = ROOT / "data" / "raw" / "corpus_candidates" / "vandenakker_pqnvr"
VDA_STATS = VDA_RAW / "Original_Stats.xlsx"
VDA_PVNP = VDA_RAW / "PvNP_Data.xlsx"
VDA_SHR = VDA_RAW / "Data_SHR.xlsx"
RPCB_EFFECTS = ROOT / "data" / "raw" / "corpus_candidates" / "rpcb" / "RP_CB Final Analysis - Effect level data.csv"
SCORE_RAW = ROOT / "data" / "raw" / "corpus_candidates" / "score"
SCORE_EXTRACTED_CLAIMS_GZ = SCORE_RAW / "extracted_claims.csv.gz"
SCORE_EXTRACTED_CLAIMS_CSV = SCORE_RAW / "extracted_claims.csv"
SCORE_EXTRACTED_CLAIMS = SCORE_EXTRACTED_CLAIMS_GZ if SCORE_EXTRACTED_CLAIMS_GZ.exists() else SCORE_EXTRACTED_CLAIMS_CSV
SCORE_ORIG_PREREG = SCORE_RAW / "orig_prereg-indicated.csv"
SCORE_METADATA = SCORE_RAW / "paper_metadata.csv"
PUBLISHED_PAPERS = ROOT / "data" / "derived" / "corpus_candidates" / "candidate_d_n_papers.csv"

SCHEEL_OUT = DATASET_DIR / "plot3_scheel_quote_stat_rescue_candidates.csv"
VDA_OUT = DATASET_DIR / "plot3_vandenakker_first_stat_candidates.csv"
VDA_MEDIAN_OUT = DATASET_DIR / "plot3_vandenakker_matched_result_median_candidates.csv"
RPCB_OUT = DATASET_DIR / "plot3_rpcb_preclinical_paper_level_candidates.csv"
SCORE_TEXT_OUT = DATASET_DIR / "plot3_score_text_claim_rescue_candidates.csv"
SUMMARY_OUT = DATASET_DIR / "plot3_rescue_candidate_summary.csv"

T_RE = re.compile(r"(?i)\bt\s*\(\s*(?P<df>\d+(?:\.\d+)?)\s*\)\s*[=≈]\s*(?P<t>-?\d+(?:\.\d+)?)")
F_RE = re.compile(
    r"(?i)\bF\s*\(\s*(?P<df1>\d+(?:\.\d+)?)\s*,\s*(?P<df2>\d+(?:\.\d+)?)\s*\)\s*[=≈]\s*(?P<f>-?\d+(?:\.\d+)?)"
)
D_RE = re.compile(r"(?i)(?:cohen'?s\s+)?\bd\s*[=≈]\s*(?P<d>-?\d+(?:\.\d+)?)")
N_RE = re.compile(r"(?i)\bN\s*[=≈]\s*(?P<n>\d{2,6})")
DN_PAIR_RE = re.compile(
    r"(?i)(?:cohen'?s\s+)?\bd\s*[=≈]\s*(?P<d>[−-]?\d+(?:\.\d+)?).{0,120}?\bN\s*[=≈]\s*(?P<n>\d{2,6})"
)
SCORE_D_RE = re.compile(
    r"(?i)(?:cohen[’']?s\s+)?\bd(?:_unb)?\s*[=≈]\s*(?P<d>[−-]?(?:\d+(?:\.\d+)?|\.\d+))"
)
SCORE_SMD_RE = re.compile(r"(?i)\bSMD\s*[=≈]\s*(?P<d>[−-]?(?:\d+(?:\.\d+)?|\.\d+))")
SCORE_R_RE = re.compile(r"(?i)\br\s*[=≈]\s*(?P<r>[−-]?(?:\d+(?:\.\d+)?|\.\d+))")
SCORE_PHI_RE = re.compile(r"(?i)(?:\bphi\b|ϕ)\s*[=≈]\s*(?P<phi>[−-]?(?:\d+(?:\.\d+)?|\.\d+))")
SCORE_OR_RE = re.compile(r"(?i)(?:odds\s*ratio|\bOR\b)\s*[=≈]\s*(?P<or>\d+(?:\.\d+)?)")
SCORE_N_DIGIT_RE = re.compile(r"(?i)\b(?:N|n|obs(?:ervations)?|participants|students|subjects)\s*[=:]?\s*(?P<n>\d[\d,]*)")
SCORE_N_TRAILING_RE = re.compile(r"(?i)\b(?P<n>\d[\d,]*)\s+(?:participants|students|subjects|children|couples)\b")
WIDE_NUMBER_RE = r"[−-]?(?:\d+(?:\.\d+)?|\.\d+)"
VDA_D_TEXT_RE = re.compile(rf"(?i)(?:cohen[’']?s\s+)?\bdz?\s*[=≈]\s*(?P<d>{WIDE_NUMBER_RE})")
VDA_G_TEXT_RE = re.compile(rf"(?i)(?:hedges[’']?\s+)?\bg\s*[=≈]\s*(?P<g>{WIDE_NUMBER_RE})")
VDA_T_TEXT_RE = re.compile(rf"(?i)\bt\s*\(\s*(?P<df>\d+(?:\.\d+)?)\s*\)\s*[=≈]\s*(?P<t>{WIDE_NUMBER_RE})")
VDA_F_TEXT_RE = re.compile(
    rf"(?i)\bF\s*\(\s*(?P<df1>\d+(?:\.\d+)?)\s*,\s*(?P<df2>\d+(?:\.\d+)?)\s*\)\s*[=≈]\s*(?P<f>{WIDE_NUMBER_RE})"
)
VDA_R_TEXT_RE = re.compile(
    rf"(?i)(?:\br\s*[=≈]\s*|\br\s*\(\s*\d+(?:\.\d+)?\s*\)\s*[=≈]\s*)(?P<r>{WIDE_NUMBER_RE})"
)
VDA_CHI2_TEXT_RE = re.compile(
    rf"(?i)(?:χ|x|chi)\s*(?:\^?2|²|square)?\s*\(\s*(?P<df>\d+(?:\.\d+)?)\s*(?:,\s*N\s*=\s*(?P<n>\d+))?\s*\)\s*[=≈]\s*(?P<chi>{WIDE_NUMBER_RE})"
)
VDA_OR_TEXT_RE = re.compile(r"(?i)(?:odds\s*ratio|\bOR\b)\s*[=≈]\s*(?P<or>\d+(?:\.\d+)?)")

NUMBER_WORDS = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
}


def num(value: object) -> float | None:
    if pd.isna(value):
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(out):
        return None
    return out


def parse_float(value: str) -> float:
    return float(value.replace("−", "-"))


def d_from_t(t_value: float, df: float) -> float | None:
    if df <= 0:
        return None
    return abs(2 * t_value / math.sqrt(df))


def d_from_f(f_value: float, df1: float, df2: float) -> float | None:
    if df1 != 1 or df2 <= 0 or f_value < 0:
        return None
    return abs(2 * math.sqrt(f_value / df2))


def d_from_r(r_value: float) -> float | None:
    if abs(r_value) >= 1:
        return None
    return abs(2 * r_value / math.sqrt(1 - r_value**2))


def d_from_or(or_value: float) -> float | None:
    if or_value <= 0:
        return None
    return abs(math.log(or_value) * math.sqrt(3) / math.pi)


def compact_text(parts: list[object]) -> str:
    return " ".join(" ".join(str(part).replace("\n", " ").split()) for part in parts if not pd.isna(part)).strip()


def parse_number_words(text: str) -> int | None:
    normalized = re.sub(r"[-–—]", " ", text.lower())
    tokens = re.findall(r"[a-z]+", normalized)
    if not tokens:
        return None
    total = 0
    current = 0
    seen = False
    for token in tokens:
        if token in NUMBER_WORDS:
            current += NUMBER_WORDS[token]
            seen = True
        elif token == "hundred" and seen:
            current = max(current, 1) * 100
        elif token == "and" and seen:
            continue
        elif seen:
            break
    total += current
    return total if seen and total > 0 else None


def parse_score_n(text: object) -> tuple[float | None, str]:
    if pd.isna(text):
        return None, "missing"
    cleaned = str(text).replace("\u2212", "-")
    digit_match = SCORE_N_DIGIT_RE.search(cleaned) or SCORE_N_TRAILING_RE.search(cleaned)
    if digit_match:
        return float(digit_match.group("n").replace(",", "")), "sample_text_digits"
    word_n = parse_number_words(cleaned)
    if word_n is not None:
        return float(word_n), "sample_text_words"
    return None, "missing"


def parse_score_effect(text: object) -> tuple[float | None, str, float | None, str]:
    if pd.isna(text):
        return None, "", None, ""
    cleaned = str(text).replace("\u2212", "-").replace("−", "-")
    for regex, stat_type, method in [
        (SCORE_D_RE, "reported_d", "reported_d"),
        (SCORE_SMD_RE, "reported_smd", "reported_smd"),
    ]:
        match = regex.search(cleaned)
        if match:
            value = abs(parse_float(match.group("d")))
            return value, stat_type, value, method
    match = SCORE_R_RE.search(cleaned)
    if match:
        r_value = parse_float(match.group("r"))
        d_value = d_from_r(r_value)
        return d_value, "r", r_value, "r_to_d"
    match = SCORE_PHI_RE.search(cleaned)
    if match:
        phi = parse_float(match.group("phi"))
        d_value = d_from_r(phi)
        return d_value, "phi", phi, "phi_to_d"
    match = SCORE_OR_RE.search(cleaned)
    if match:
        or_value = float(match.group("or"))
        d_value = d_from_or(or_value)
        return d_value, "odds_ratio", or_value, "chinn_log_or_to_d"
    return None, "", None, ""


VDA_CODER_PRIORITY = {
    "OvdAMS": 0,
    "OvdAMvA": 0,
    "OvdAMB": 0,
    "MBOvdA": 0,
    "MEMdJ": 0,
    "HOFR": 0,
    "MvAAS": 0,
    "MBAS": 0,
    "ZZZ": 0,
    "OvdA": 1,
    "ME": 1,
    "HO": 1,
    "MvA": 1,
    "MB": 1,
    "ZZ": 1,
    "MS": 2,
    "MdJ": 2,
    "FR": 2,
    "AS": 2,
    "Z": 2,
}


def parse_vandenakker_result_text(text: object, n_fallback: float | None) -> tuple[float | None, str, float | None, str]:
    """Parse D-like effects from a matched result text in the SHR workbook.

    The result text is source-coded as matching a preregistered hypothesis; this
    parser only chooses the least-loss D conversion available in the text.
    """
    if pd.isna(text):
        return None, "", None, ""
    cleaned = str(text).replace("\u2212", "-").replace("−", "-").replace("\n", " ")

    match = VDA_D_TEXT_RE.search(cleaned)
    if match:
        d_value = abs(parse_float(match.group("d")))
        return d_value, "reported_d_or_dz", d_value, "reported_d_or_dz"

    match = VDA_G_TEXT_RE.search(cleaned)
    if match:
        g_value = abs(parse_float(match.group("g")))
        return g_value, "reported_g", g_value, "reported_hedges_g"

    match = VDA_T_TEXT_RE.search(cleaned)
    if match:
        t_value = parse_float(match.group("t"))
        df = float(match.group("df"))
        d_value = d_from_t(t_value, df)
        return d_value, "t", t_value, "t_df_to_d"

    match = VDA_F_TEXT_RE.search(cleaned)
    if match:
        f_value = parse_float(match.group("f"))
        df1 = float(match.group("df1"))
        df2 = float(match.group("df2"))
        d_value = d_from_f(f_value, df1, df2)
        return d_value, "F", f_value, "F_1_df_to_d"

    match = VDA_R_TEXT_RE.search(cleaned)
    if match:
        r_value = parse_float(match.group("r"))
        d_value = d_from_r(r_value)
        return d_value, "r", r_value, "r_to_d"

    match = VDA_CHI2_TEXT_RE.search(cleaned)
    if match and float(match.group("df")) == 1:
        n_value = float(match.group("n")) if match.group("n") else n_fallback
        chi_value = parse_float(match.group("chi"))
        if n_value is not None and n_value > 0 and chi_value >= 0:
            phi = math.sqrt(chi_value / n_value)
            d_value = d_from_r(phi)
            return d_value, "chi_square", chi_value, "chi2_with_publication_n_to_d"

    match = VDA_OR_TEXT_RE.search(cleaned)
    if match:
        or_value = float(match.group("or"))
        d_value = d_from_or(or_value)
        return d_value, "odds_ratio", or_value, "chinn_log_or_to_d"

    return None, "", None, ""


def build_scheel_candidates() -> pd.DataFrame:
    if not SCHEEL_TSV.exists():
        return pd.DataFrame()
    df = pd.read_csv(SCHEEL_TSV, sep="\t")
    rr = df[(df["is_RR"] == 1) & (df["include_in_analysis"] == 1)].copy()
    rows: list[dict[str, object]] = []

    for _, row in rr.iterrows():
        quote = compact_text([row.get("hypothesis_quote"), row.get("result_quote"), row.get("finding"), row.get("conclusion")])
        n_match = N_RE.search(quote)
        n_quote = int(n_match.group("n")) if n_match else None

        candidates: list[dict[str, object]] = []
        dn_pairs = list(DN_PAIR_RE.finditer(quote))
        if dn_pairs:
            for pair in dn_pairs:
                d_val = abs(parse_float(pair.group("d")))
                candidates.append(
                    {
                        "stat_type": "reported_d",
                        "stat_value": d_val,
                        "df1": None,
                        "df2": None,
                        "D_candidate": d_val,
                        "N_candidate": int(pair.group("n")),
                        "N_candidate_basis": "quote_d_n_pair",
                        "conversion_method": "reported_d",
                    }
                )
        else:
            d_match = D_RE.search(quote)
            if d_match:
                d_val = abs(parse_float(d_match.group("d")))
                candidates.append(
                    {
                        "stat_type": "reported_d",
                        "stat_value": d_val,
                        "df1": None,
                        "df2": None,
                        "D_candidate": d_val,
                        "N_candidate": n_quote,
                        "N_candidate_basis": "quote_N" if n_quote else "missing",
                        "conversion_method": "reported_d",
                    }
                )

        f_match = F_RE.search(quote)
        if f_match:
            df1 = float(f_match.group("df1"))
            df2 = float(f_match.group("df2"))
            f_val = float(f_match.group("f"))
            d_val = d_from_f(f_val, df1, df2)
            if d_val is not None:
                candidates.append(
                    {
                        "stat_type": "F",
                        "stat_value": f_val,
                        "df1": df1,
                        "df2": df2,
                        "D_candidate": d_val,
                        "N_candidate": n_quote or int(round(df2 + 2)),
                        "N_candidate_basis": "quote_N" if n_quote else "df2_plus_2_approx",
                        "conversion_method": "F_1_df_to_d",
                    }
                )

        t_match = T_RE.search(quote)
        if t_match:
            df_t = float(t_match.group("df"))
            t_val = float(t_match.group("t"))
            d_val = d_from_t(t_val, df_t)
            if d_val is not None:
                candidates.append(
                    {
                        "stat_type": "t",
                        "stat_value": t_val,
                        "df1": df_t,
                        "df2": None,
                        "D_candidate": d_val,
                        "N_candidate": n_quote or int(round(df_t + 2)),
                        "N_candidate_basis": "quote_N" if n_quote else "df_plus_2_approx",
                        "conversion_method": "t_df_to_d",
                    }
                )

        for i, candidate in enumerate(candidates, start=1):
            has_exact_n = candidate["N_candidate_basis"] in {"quote_N", "quote_d_n_pair"}
            rows.append(
                {
                    "candidate_id": f"scheel_rr_{int(row['id']):03d}_{i}",
                    "source_family": "Scheel et al. 2021 Registered Reports corpus",
                    "source_file": str(SCHEEL_TSV.relative_to(ROOT)),
                    "scheel_id": row.get("id"),
                    "title": row.get("title"),
                    "doi": row.get("doi"),
                    "support_binary": row.get("support_binary"),
                    "candidate_status": "needs_pdf_n_check" if not has_exact_n else "needs_pdf_focal_check",
                    "strict_append_ready": False,
                    "remaining_blocker": (
                        "N is approximated from test degrees of freedom; verify analytic N and first-hypothesis mapping in the article."
                        if not has_exact_n
                        else "Quote contains a candidate D/N, but article PDF still needs first-hypothesis and analytic-N verification."
                    ),
                    "quote": quote,
                    **candidate,
                }
            )

    out = pd.DataFrame(rows)
    if not out.empty:
        out = out.sort_values(["scheel_id", "candidate_id"]).reset_index(drop=True)
    return out


def build_vandenakker_candidates() -> pd.DataFrame:
    if not (VDA_STATS.exists() and VDA_PVNP.exists()):
        return pd.DataFrame()
    stats = pd.read_excel(VDA_STATS)
    pvnp = pd.read_excel(VDA_PVNP)
    stats = stats.reset_index(names="source_row")
    merged = stats.merge(
        pvnp[["ID", "TitleOriginal", "DOIOriginal", "JournalOriginal", "NOriginal", "PositiveOriginal"]],
        left_on="PSP",
        right_on="ID",
        how="left",
    )

    rows: list[dict[str, object]] = []
    for _, row in merged.iterrows():
        n = num(row.get("NOriginal"))
        if n is None or n <= 0:
            continue

        d_val = None
        method = None
        stat_type = None
        stat_value = None
        df1 = num(row.get("df1"))
        df2 = num(row.get("df2"))
        t_val = num(row.get("t"))
        f_val = num(row.get("F"))
        r_val = num(row.get("cor"))

        if t_val is not None and df1 is not None:
            d_val = d_from_t(t_val, df1)
            method = "t_df_to_d"
            stat_type = "t"
            stat_value = t_val
        elif f_val is not None and df1 == 1 and df2 is not None:
            d_val = d_from_f(f_val, df1, df2)
            method = "F_1_df_to_d"
            stat_type = "F"
            stat_value = f_val
        elif r_val is not None and abs(r_val) > 1e-12:
            d_val = d_from_r(r_val)
            method = "r_to_d"
            stat_type = "r"
            stat_value = r_val

        if d_val is None:
            continue
        rows.append(
            {
                "candidate_id": f"vandenakker_psp_{int(row['PSP']):03d}_row_{int(row['source_row']) + 2}",
                "source_family": "van den Akker preregistration-in-practice parsed original statistics",
                "source_file": str(VDA_STATS.relative_to(ROOT)),
                "PSP": row.get("PSP"),
                "source_row": int(row["source_row"]) + 2,
                "title": row.get("TitleOriginal"),
                "doi": row.get("DOIOriginal"),
                "journal": row.get("JournalOriginal"),
                "candidate_status": "stage_focal_selector_needed",
                "strict_append_ready": False,
                "remaining_blocker": "First convertible statistic per PSP is not yet proven to be the first preregistered confirmatory hypothesis; DOI-level deduplication is also pending.",
                "statistical_statement": compact_text([row.get("Statistical statement")]),
                "stat_type": stat_type,
                "stat_value": stat_value,
                "df1": df1,
                "df2": df2,
                "D_candidate": d_val,
                "N_candidate": n,
                "conversion_method": method,
                "positive_original": row.get("PositiveOriginal"),
            }
        )

    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out = out.sort_values(["PSP", "source_row"]).drop_duplicates("PSP", keep="first").reset_index(drop=True)
    return out


def build_vandenakker_matched_result_median_candidates() -> pd.DataFrame:
    """Build paper-median rows from result texts matched to preregistered hypotheses.

    Data_SHR.xlsx is the source that makes this usable under the relaxed policy:
    it codes whether each publication result matched a preregistered hypothesis.
    We keep all parseable matched result statistics, deduplicate duplicated coder
    rows by PSP/result slot, then collapse to one median D row per PSP/paper.
    """
    if not (VDA_SHR.exists() and VDA_PVNP.exists()):
        return pd.DataFrame()
    try:
        shr = pd.read_excel(VDA_SHR, sheet_name="Part 4")
    except ValueError:
        return pd.DataFrame()
    pvnp = pd.read_excel(VDA_PVNP)
    metadata = pvnp[
        ["ID", "TitleOriginal", "DOIOriginal", "JournalOriginal", "NOriginal", "PositiveOriginal"]
    ].copy()
    metadata["NOriginal"] = pd.to_numeric(metadata["NOriginal"], errors="coerce")
    metadata = metadata[metadata["NOriginal"] > 0].copy()
    n_by_psp = dict(zip(metadata["ID"], metadata["NOriginal"]))
    valid_psps = set(n_by_psp)

    result_indices = sorted(
        int(match.group(1))
        for column in shr.columns
        if (match := re.match(r"ResultText_(\d+)$", str(column)))
    )
    statistic_rows: list[dict[str, object]] = []
    for source_index, row in shr.loc[shr["PSP"].isin(valid_psps)].iterrows():
        psp = int(row["PSP"])
        n_value = float(n_by_psp[psp])
        coder = str(row.get("Initials", ""))
        coder_priority = VDA_CODER_PRIORITY.get(coder, 9)
        for result_index in result_indices:
            result_text = row.get(f"ResultText_{result_index}")
            if pd.isna(result_text) or not str(result_text).strip():
                continue
            match_flag = str(row.get(f"Match_{result_index}", ""))
            if not match_flag.startswith("Yes"):
                continue
            d_value, stat_type, stat_value, conversion_method = parse_vandenakker_result_text(result_text, n_value)
            if d_value is None or d_value <= 0:
                continue
            statistic_rows.append(
                {
                    "PSP": psp,
                    "result_index": result_index,
                    "coder": coder,
                    "coder_priority": coder_priority,
                    "source_excel_row": int(source_index) + 2,
                    "match_flag": match_flag,
                    "support_flag": row.get(f"Support_{result_index}"),
                    "as_predicted_flag": row.get(f"AsPredicted_{result_index}"),
                    "importance_flag": row.get(f"Importance_{result_index}"),
                    "replication_flag": row.get(f"Replication_{result_index}"),
                    "label_flag": row.get(f"Label_{result_index}"),
                    "stat_type": stat_type,
                    "stat_value": stat_value,
                    "D_result": d_value,
                    "N_result": n_value,
                    "conversion_method": conversion_method,
                    "result_text": compact_text([result_text])[:500],
                }
            )

    if not statistic_rows:
        return pd.DataFrame()
    stats = pd.DataFrame(statistic_rows)
    stats = stats.sort_values(["PSP", "result_index", "coder_priority", "source_excel_row"])
    stats = stats.drop_duplicates(["PSP", "result_index"], keep="first").reset_index(drop=True)
    merged = stats.merge(metadata, left_on="PSP", right_on="ID", how="left")

    rows: list[dict[str, object]] = []
    for psp, group in merged.groupby("PSP", sort=True):
        group = group.sort_values("result_index")
        methods = "; ".join(sorted(set(group["conversion_method"].dropna().astype(str))))
        stat_types = "; ".join(sorted(set(group["stat_type"].dropna().astype(str))))
        examples = " || ".join(group["result_text"].dropna().astype(str).head(3))
        rows.append(
            {
                "candidate_id": f"vandenakker_psp_{int(psp):03d}_matched_result_median",
                "source_family": "van den Akker matched preregistered-result paper medians",
                "source_file": f"{VDA_SHR.relative_to(ROOT)}; {VDA_PVNP.relative_to(ROOT)}",
                "PSP": int(psp),
                "title": group["TitleOriginal"].dropna().iloc[0] if group["TitleOriginal"].notna().any() else "",
                "doi": group["DOIOriginal"].dropna().iloc[0] if group["DOIOriginal"].notna().any() else "",
                "journal": group["JournalOriginal"].dropna().iloc[0] if group["JournalOriginal"].notna().any() else "",
                "candidate_status": "paper_median_matched_preregistered_result_ready",
                "strict_append_ready": True,
                "remaining_blocker": "",
                "matched_result_rows": len(group),
                "matched_result_indices": ";".join(str(int(value)) for value in group["result_index"].tolist()),
                "stat_types": stat_types,
                "conversion_methods": methods,
                "D_candidate": float(group["D_result"].median()),
                "N_candidate": float(group["N_result"].median()),
                "N_candidate_basis": "PvNP_Data.NOriginal_publication_sample_size",
                "positive_original": group["PositiveOriginal"].dropna().iloc[0] if group["PositiveOriginal"].notna().any() else "",
                "result_text_examples": examples,
            }
        )

    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out = out.sort_values(["PSP"]).reset_index(drop=True)
    return out


def build_rpcb_candidates() -> pd.DataFrame:
    if not RPCB_EFFECTS.exists():
        return pd.DataFrame()
    df = pd.read_csv(RPCB_EFFECTS)
    rows = df[
        df["Replication sample size"].notna()
        & df["Replication effect size (SMD)"].notna()
        & df["Paper #"].notna()
    ].copy()
    rows["D_result"] = pd.to_numeric(rows["Replication effect size (SMD)"], errors="coerce").abs()
    rows["N_result"] = pd.to_numeric(rows["Replication sample size"], errors="coerce")
    rows = rows[(rows["D_result"] > 0) & (rows["N_result"] > 0)].copy()
    rows = rows.sort_values(["Paper #", "Experiment #", "Effect #", "Internal replication #"])

    collapsed = []
    for paper_number, group in rows.groupby("Paper #", sort=True):
        first = group.iloc[0]
        collapsed.append(
            {
                "candidate_id": f"rpcb_paper_{int(paper_number):02d}_median_registered_effect",
                "source_family": "Reproducibility Project: Cancer Biology Stage-2 Registered Report effects",
                "source_file": str(RPCB_EFFECTS.relative_to(ROOT)),
                "paper_number": paper_number,
                "experiment_number": first.get("Experiment #"),
                "effect_number": first.get("Effect #"),
                "effect_description": first.get("Effect description"),
                "candidate_status": "paper_median_registered_report_result_ready",
                "strict_append_ready": True,
                "remaining_blocker": "",
                "registered_result_rows": len(group),
                "stat_type": "; ".join(sorted(set(group["Effect size type (SMD)"].dropna().astype(str)))),
                "stat_value": float(group["D_result"].median()),
                "D_candidate": float(group["D_result"].median()),
                "N_candidate": float(group["N_result"].median()),
                "conversion_method": "median_reported_replication_smd_per_paper",
                "replication_p_value": (
                    group["Replication p value (SMD)"].dropna().iloc[0]
                    if group["Replication p value (SMD)"].notna().any()
                    else ""
                ),
            }
        )

    out = pd.DataFrame(collapsed)
    return out


def current_score_paper_ids() -> set[str]:
    if not (PUBLISHED_PAPERS.exists() and SCORE_ORIG_PREREG.exists() and SCORE_METADATA.exists()):
        return set()
    prereg = pd.read_csv(SCORE_ORIG_PREREG)
    metadata = pd.read_csv(SCORE_METADATA)
    published = pd.read_csv(PUBLISHED_PAPERS)
    if not {"paper_id", "prereg"}.issubset(prereg.columns) or not {"paper_id", "DOI"}.issubset(metadata.columns):
        return set()
    prereg_true = prereg.loc[prereg["prereg"].astype(str).str.lower().eq("true"), ["paper_id"]].drop_duplicates()
    metadata = metadata[["paper_id", "DOI"]].copy()
    metadata["doi_norm"] = metadata["DOI"].astype(str).str.lower().str.strip()
    score = published.loc[published["source_corpus"].eq("score_cos_claims")].copy()
    if score.empty:
        return set()
    score = score[
        (pd.to_numeric(score.get("D_median", pd.Series(dtype=float)), errors="coerce") > 0)
        & (pd.to_numeric(score.get("N_median", pd.Series(dtype=float)), errors="coerce") > 0)
    ].copy()
    score["doi_norm"] = score["unit_id"].astype(str).str.replace(r"^DOI:", "", regex=True).str.lower().str.strip()
    score = score.merge(metadata, on="doi_norm", how="left").merge(prereg_true, on="paper_id", how="inner")
    return set(score["paper_id"].dropna().astype(str))


def build_score_text_claim_candidates() -> pd.DataFrame:
    if not (SCORE_EXTRACTED_CLAIMS.exists() and SCORE_ORIG_PREREG.exists() and SCORE_METADATA.exists()):
        return pd.DataFrame()
    claims = pd.read_csv(SCORE_EXTRACTED_CLAIMS, low_memory=False)
    prereg = pd.read_csv(SCORE_ORIG_PREREG)
    metadata = pd.read_csv(SCORE_METADATA)
    if "paper_id" not in claims.columns or "paper_id" not in prereg.columns or "prereg" not in prereg.columns:
        return pd.DataFrame()

    prereg_true = prereg.loc[prereg["prereg"].astype(str).str.lower().eq("true"), ["paper_id"]].drop_duplicates()
    meta_cols = [col for col in ["paper_id", "title", "publication_standard", "pub_year", "DOI", "citation"] if col in metadata.columns]
    merged = claims.merge(prereg_true, on="paper_id", how="inner")
    if meta_cols:
        merged = merged.merge(metadata[meta_cols].drop_duplicates("paper_id"), on="paper_id", how="left")
    represented = current_score_paper_ids()

    rows: list[dict[str, object]] = []
    for _, row in merged.iterrows():
        sample_text = compact_text([row.get("coded_sample_size"), row.get("sample_size")])
        effect_text = compact_text([row.get("coded_effect_size"), row.get("effect_size"), row.get("coded_stat_evidence")])
        n_value, n_basis = parse_score_n(sample_text)
        d_value, stat_type, stat_value, method = parse_score_effect(effect_text)
        if d_value is None or n_value is None:
            continue
        already_represented = str(row.get("paper_id")) in represented
        strict_ready = (
            not already_represented
            and n_basis in {"sample_text_digits", "sample_text_words"}
            and method in {"reported_d", "reported_smd", "r_to_d", "phi_to_d", "chinn_log_or_to_d"}
            and n_value >= 10
        )
        if already_represented:
            status = "already_represented_in_score_paper_join"
            blocker = "This preregistration-indicated SCORE paper already has a deduplicated D/N row in strict Plot 3."
        elif strict_ready:
            status = "score_text_strict_append_ready"
            blocker = "None under the current SCORE paper-level preregistration-indicated rule; claim-specific preregistration mapping remains a source-family caveat."
        else:
            status = "stage_metric_or_n_check"
            blocker = "Candidate has parseable D/N text, but the N or effect metric still needs manual validation before strict inclusion."

        rows.append(
            {
                "candidate_id": f"score_text_{safe_id(str(row.get('paper_id')))}_{safe_id(str(row.get('unique_claim_id')))}",
                "source_family": "SCORE/COS preregistration-indicated extracted claim text",
                "source_file": str(SCORE_EXTRACTED_CLAIMS.relative_to(ROOT)),
                "paper_id": row.get("paper_id"),
                "claim_id": row.get("unique_claim_id"),
                "title": row.get("title"),
                "doi": row.get("DOI"),
                "journal": row.get("publication_standard"),
                "pub_year": row.get("pub_year"),
                "citation": row.get("citation"),
                "candidate_status": status,
                "strict_append_ready": strict_ready,
                "remaining_blocker": blocker,
                "sample_size_text": sample_text,
                "effect_size_text": effect_text,
                "p_value_text": compact_text([row.get("coded_p_value"), row.get("p_value")]),
                "stat_type": stat_type,
                "stat_value": stat_value,
                "D_candidate": d_value,
                "N_candidate": n_value,
                "N_candidate_basis": n_basis,
                "conversion_method": method,
                "already_represented_in_score_paper_join": already_represented,
            }
        )

    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out = out.sort_values(
        ["strict_append_ready", "already_represented_in_score_paper_join", "paper_id", "claim_id"],
        ascending=[False, True, True, True],
    ).reset_index(drop=True)
    return out


def safe_id(value: str) -> str:
    out = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_").lower()
    return out or "row"


def write_outputs() -> None:
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    outputs = {
        "scheel_quote_stat_candidates": (build_scheel_candidates(), SCHEEL_OUT),
        "vandenakker_first_stat_candidates": (build_vandenakker_candidates(), VDA_OUT),
        "vandenakker_matched_result_median_candidates": (
            build_vandenakker_matched_result_median_candidates(),
            VDA_MEDIAN_OUT,
        ),
        "rpcb_preclinical_paper_level_candidates": (build_rpcb_candidates(), RPCB_OUT),
        "score_text_claim_candidates": (build_score_text_claim_candidates(), SCORE_TEXT_OUT),
    }
    summary_rows = []
    for name, (df, path) in outputs.items():
        df.to_csv(path, index=False)
        summary_rows.append(
            {
                "candidate_table": name,
                "path": str(path.relative_to(ROOT)),
                "rows": len(df),
                "rows_with_D": int(df["D_candidate"].notna().sum()) if "D_candidate" in df else 0,
                "rows_with_N": int(df["N_candidate"].notna().sum()) if "N_candidate" in df else 0,
                "strict_append_ready": int(df["strict_append_ready"].sum()) if "strict_append_ready" in df else 0,
                "candidate_statuses": "; ".join(
                    f"{status}={count}"
                    for status, count in (
                        df["candidate_status"].value_counts().sort_index().items()
                        if "candidate_status" in df
                        else []
                    )
                ),
            }
        )
    pd.DataFrame(summary_rows).to_csv(SUMMARY_OUT, index=False)


def main() -> None:
    write_outputs()


if __name__ == "__main__":
    main()
