#!/usr/bin/env python3
"""Build the complete GPT prompt for blocked individual-replication rows."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
WORKLIST_DIR = ROOT / "steps" / "individual_replication_papers" / "figure1"
AUTO_DIR = WORKLIST_DIR / "auto_mining"
PROMOTION_PROPOSAL = WORKLIST_DIR / "individual-paper-promotion-proposal.tsv"
GPT_HANDOFF = AUTO_DIR / "individual-paper-gpt-handoff-after-auto-mining.tsv"
GPT_DECISIONS = AUTO_DIR / "individual-paper-gpt-decisions-after-auto-mining-2026-05-06.tsv"
OUT_MD = ROOT / "reports" / "figure1_individual_replication_blocker_unblock_prompt_2026-05-06.md"
OUT_STEPS_MD = AUTO_DIR / "individual-paper-gpt-blocker-unblock-prompt-2026-05-06.md"
OUT_JSON = AUTO_DIR / "individual-paper-gpt-blocker-unblock-candidates-2026-05-06.json"


OUTPUT_SCHEMA = {
    "candidate_id": "",
    "decision": "ready_for_row|needs_more_evidence|native_only|coverage_only|reject",
    "replication_kind": "direct_replication|close_replication|clinical_followup|clinical_reversal|independent_validation|genetics_replication_cohort|other",
    "row_policy": "strict_figure1a|d_equivalent_figure1b|native_only|coverage_only|reject",
    "original": {
        "title": "",
        "authors_year": "",
        "doi": "",
        "pmid": "",
        "pmcid": "",
        "registry_id": "",
        "study_or_experiment": "",
        "outcome": "",
        "contrast": "",
        "timepoint": "",
        "population": "",
        "n": "",
        "n_by_arm": {},
        "effect": "",
        "effect_metric": "",
        "event_counts": {
            "treatment_events": None,
            "treatment_total": None,
            "control_events": None,
            "control_total": None,
        },
        "verbatim_effect_text": "",
        "verbatim_n_text": "",
        "verbatim_selector_text": "",
        "source_url": "",
        "locator": "",
    },
    "replication": {
        "title": "",
        "authors_year": "",
        "doi": "",
        "pmid": "",
        "pmcid": "",
        "registry_id": "",
        "study_or_experiment": "",
        "outcome": "",
        "contrast": "",
        "timepoint": "",
        "population": "",
        "n": "",
        "n_by_arm": {},
        "effect": "",
        "effect_metric": "",
        "event_counts": {
            "treatment_events": None,
            "treatment_total": None,
            "control_events": None,
            "control_total": None,
        },
        "verbatim_effect_text": "",
        "verbatim_n_text": "",
        "verbatim_selector_text": "",
        "source_url": "",
        "locator": "",
    },
    "relationship_evidence": {
        "evidence_type": "title_exact_replication|abstract_direct_replication|abstract_failed_replication|methods_original_study_mapping|methods_original_materials|table_pair_mapping|clinical_confirmatory_trial|clinical_reversal_followup|trial_registry_reference|repository_readme|other",
        "verbatim_text": "",
        "source_url": "",
        "locator": "",
        "strength_0_to_5": None,
    },
    "conversion": {
        "route": "native_d|means_sds_to_d|t_to_d|f_to_d|r_to_d|event_counts_to_logor_to_d|or_to_d|rr_with_baseline_to_or_to_d|native_only|none",
        "formula": "",
        "computed_original_d": None,
        "computed_replication_d": None,
        "figure1_original_d_magnitude": None,
        "figure1_replication_d_magnitude": None,
        "assumptions": [],
    },
    "source_objects_to_mirror": [
        {
            "url": "",
            "object_type": "html|pdf|pmc_xml|supplement|dataset|registry_json|accepted_manuscript|preprint|repository|other",
            "why_needed": "",
        }
    ],
    "blockers": [],
    "dedupe_or_overlap_notes": "",
    "notes": "",
}


def clean(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).replace("\t", " ").replace("\r", " ").strip()


def read_tsv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False).fillna("")


def indexed(df: pd.DataFrame) -> dict[str, dict[str, Any]]:
    if df.empty or "candidate_id" not in df.columns:
        return {}
    return df.drop_duplicates("candidate_id", keep="last").set_index("candidate_id", drop=False).to_dict(orient="index")


def split_urls(value: Any) -> list[str]:
    text = clean(value)
    if not text:
        return []
    if text.startswith("["):
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return [clean(item) for item in parsed if clean(item)]
        except json.JSONDecodeError:
            pass
    return [part.strip() for part in text.split("|") if part.strip()]


def first_nonempty(*values: Any) -> str:
    for value in values:
        text = clean(value)
        if text:
            return text
    return ""


def build_candidates() -> list[dict[str, Any]]:
    decisions = read_tsv(GPT_DECISIONS)
    handoff = indexed(read_tsv(GPT_HANDOFF))
    proposal = read_tsv(PROMOTION_PROPOSAL)
    proposal = proposal[proposal.get("promotion_decision", "").ne("promote_to_harvested_pair_contract")].copy()
    proposal_by_candidate = indexed(proposal)

    if decisions.empty:
        raise FileNotFoundError(f"Missing GPT decision receipt: {GPT_DECISIONS}")

    candidates: list[dict[str, Any]] = []
    for _, decision in decisions.iterrows():
        candidate_id = clean(decision.get("candidate_id"))
        if clean(decision.get("local_verifier_action")) == "promoted":
            continue
        h = handoff.get(candidate_id, {})
        p = proposal_by_candidate.get(candidate_id, {})
        source_urls = split_urls(first_nonempty(h.get("source_object_urls")))
        local_paths = first_nonempty(p.get("local_support_paths"), h.get("local_file_summary"))
        candidates.append(
            {
                "candidate_id": candidate_id,
                "prior_gpt_decision": clean(decision.get("gpt_decision")),
                "prior_row_policy": clean(decision.get("row_policy")),
                "prior_replication_kind": clean(decision.get("replication_kind")),
                "local_verifier_action": clean(decision.get("local_verifier_action")),
                "local_reason": clean(decision.get("reason")),
                "candidate_name": first_nonempty(h.get("candidate_name"), p.get("outcome"), p.get("replication_title")),
                "candidate_route": first_nonempty(h.get("candidate_route"), clean(decision.get("row_policy"))),
                "current_local_scan_decision": first_nonempty(p.get("scan_decision"), h.get("scan_decision")),
                "original_title": first_nonempty(p.get("original_title"), h.get("original_title")),
                "original_doi": first_nonempty(p.get("original_doi"), h.get("original_doi")),
                "replication_title": first_nonempty(p.get("replication_title"), h.get("replication_title")),
                "replication_doi": first_nonempty(p.get("replication_doi"), h.get("replication_doi")),
                "outcome_or_result_option": first_nonempty(p.get("outcome"), h.get("candidate_name")),
                "current_numeric_fields_if_any": {
                    "D_original": clean(p.get("D_original")),
                    "N_original": clean(p.get("N_original")),
                    "D_replication": clean(p.get("D_replication")),
                    "N_replication": clean(p.get("N_replication")),
                },
                "current_blocker": first_nonempty(h.get("blocker"), p.get("next_action"), decision.get("reason")),
                "known_original_support_text": first_nonempty(p.get("original_support_text"), h.get("known_original_support_text")),
                "known_replication_support_text": first_nonempty(p.get("replication_support_text"), h.get("known_replication_support_text")),
                "conversion_or_policy_note": first_nonempty(p.get("conversion_or_policy_note"), h.get("conversion_or_policy_note")),
                "source_object_urls_from_search": source_urls,
                "local_source_file_summary_or_paths": local_paths,
                "requested_gpt_action": first_nonempty(
                    h.get("gpt_task"),
                    "Find value-bearing source objects and exact matched original/replication D/N or event-count inputs; otherwise explain why this cannot be a row.",
                ),
                "expected_json_decision_values": first_nonempty(
                    h.get("expected_json_decision_values"),
                    "ready_for_row | needs_more_evidence | native_only | coverage_only | reject",
                ),
            }
        )

    priority = {
        "needs_more_evidence": 0,
        "coverage_only": 1,
        "native_only": 2,
        "reject": 3,
    }
    candidates.sort(
        key=lambda row: (
            priority.get(row["prior_gpt_decision"], 9),
            row["candidate_id"],
        )
    )
    return candidates


def build_prompt(candidates: list[dict[str, Any]]) -> str:
    candidate_json = json.dumps(candidates, indent=2, ensure_ascii=False)
    schema_json = json.dumps([OUTPUT_SCHEMA], indent=2, ensure_ascii=False)
    return f"""# Figure 1 Individual Replication Blocker Unblock Prompt

Copy this whole prompt into GPT Pro. It already includes the candidates to work; do not add anything manually.

You are helping complete rows for Figure 1 of a meta-science dataset about original findings and larger replication/follow-up attempts.

Context:
We have already built and run a broad search system for individual replication papers. The discovery system is finding real candidates. The current bottleneck is not broad search strategy. The bottleneck is converting candidate paper pairs into row-level evidence with enough source grounding to plot.

Do not spend your answer designing new generic search strategies. Do not return prose. Return only valid JSON.

Goal:
For each candidate, determine whether it can become a plotted Figure 1 row now, and if so extract enough row-level information to support it.

A candidate becomes a plotted row only when there is:

1. Affirmative evidence that the replication/follow-up paper is actually retesting a specific earlier paper/result.
2. A specific original study/result/outcome/contrast mapped to a specific replication study/result/outcome/contrast.
3. Original N and replication N.
4. Original effect and replication effect on a defensible Figure 1 scale.
5. Value-bearing source objects that can be mirrored locally: full-text article, PDF, PMC/HTML/XML, supplement, OSF/Figshare/Dataverse/Zenodo data, trial registry result, accepted manuscript, or authoritative report.

Current Figure 1 routes:

- strict_figure1a:
  Use when both original and replication are D/SMD-compatible. Acceptable inputs include Cohen's d, Hedges g, SMD, means+SDs+n, mean difference+pooled SD+n, or t/F/r with df and group n if conversion is documented.

- d_equivalent_figure1b:
  Use for comparative binary/clinical outcomes when event-count or OR/RR/RD inputs support conversion to d-equivalent. Prefer event counts by arm. If using OR/logOR/RR/RD, record assumptions and required baseline-risk inputs.

- native_only:
  Use when the replication relation is real and values/N are available, but the metric is not defensibly convertible to Figure 1 D/SMD or binary d-equivalent. Examples: regression interactions, moderation models, adjusted hazard ratios without conversion inputs, AUC/model validation, unclear multi-factor native outcomes.

- coverage_only:
  Use when the relation is real but public value-bearing source objects or exact values are missing.

- reject:
  Use when there is no matched original/replication result, the source is metadata-only, review-only, same-data reanalysis, computational reproduction only, no independent replication/follow-up sample, no comparator for a binary endpoint, or the replication N is not larger under current policy.

Important rules:

- Metadata-only is not enough.
- A citation is not enough.
- A DOI landing page is not enough unless it contains the actual value-bearing text.
- Do not promote from title/abstract alone unless the title/abstract contains the exact needed N/effect values.
- Do not collapse multiple outcomes or multiple original target studies into one row.
- Preserve the exact original text before cleaning values.
- If the replication paper has several experiments, choose the cleanest matched larger-N replication for the original target, or mark the candidate as needing more evidence.
- If the replication gives a pooled/meta-analytic effect across labs or studies, use it only if the paper clearly maps that pooled estimate to the original target and the aggregation level is defensible.
- If a value is taken from a planning/power-analysis statement rather than an original result table, explicitly flag that.
- Preserve signed effects in notes and verbatim text, but Figure 1 D should be a nonnegative magnitude unless explicitly stated otherwise.
- If original and replication effects use different contrasts, mark needs_more_evidence or reject. Do not mix unmatched contrasts.
- If replication N is not larger than original N for the matched contrast, mark reject unless there is a clearly defensible larger pooled replication estimate.
- Prefer source-reported D/Hedges g/SMD when available. Otherwise compute with an explicit formula.

Useful conversion formulas:

- Independent-groups t to d:
  d = t * sqrt(1/n1 + 1/n2)
- Approximate equal-groups t to d when only total N is known:
  d approximately equals 2t / sqrt(df)
  Use only if equal groups are reasonable and flag the assumption.
- F with 1 numerator df to t:
  t = sqrt(F), then use t-to-d route if n/df support it.
- r to d:
  d = 2r / sqrt(1 - r^2)
- OR to d-equivalent:
  d = log(OR) * sqrt(3) / pi
- Event counts to OR:
  OR = (treatment_events * control_nonevents) / (treatment_nonevents * control_events)
  then OR_to_d. Note zero-cell corrections if used.

Your task for each candidate:

1. Locate or identify the best value-bearing source objects for both original and replication.
2. Resolve the exact original target: paper, study/experiment, outcome, contrast, timepoint.
3. Resolve the exact replication target: paper, study/experiment, outcome, contrast, timepoint.
4. Extract original N/effect and replication N/effect with verbatim support.
5. Compute D or d-equivalent if needed.
6. Decide: ready_for_row, needs_more_evidence, native_only, coverage_only, or reject.
7. For any non-ready candidate, state the precise missing source object or value.

Return only valid JSON: an array of candidate decision objects. Use this schema exactly:

```json
{schema_json}
```

Candidates to work:

```json
{candidate_json}
```
"""


def main() -> None:
    candidates = build_candidates()
    payload = {
        "candidate_count": len(candidates),
        "source_tables": [
            str(GPT_DECISIONS.relative_to(ROOT)),
            str(GPT_HANDOFF.relative_to(ROOT)),
            str(PROMOTION_PROPOSAL.relative_to(ROOT)),
        ],
        "candidates": candidates,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    prompt = build_prompt(candidates)
    OUT_MD.write_text(prompt, encoding="utf-8")
    OUT_STEPS_MD.write_text(prompt, encoding="utf-8")

    print(f"Wrote {OUT_MD.relative_to(ROOT)}")
    print(f"Wrote {OUT_STEPS_MD.relative_to(ROOT)}")
    print(f"Wrote {OUT_JSON.relative_to(ROOT)}")
    print(f"Candidate count: {len(candidates)}")


if __name__ == "__main__":
    main()
