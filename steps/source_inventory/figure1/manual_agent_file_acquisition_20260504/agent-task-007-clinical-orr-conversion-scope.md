# Agent Task 007: Clinical One-Arm ORR/Proportion Conversion Scope

## Objective

Research whether one-arm objective response rate (ORR) or single-arm proportion endpoints can be converted to a D-like axis under a defensible, documented rule for this Figure 1 project.

This is a scope/method task, not a file-finding task. Current local mining excludes one-arm ORR rows. The clinical highly cited workbook has 3 currently excluded ORR rows, and the broader clinical literature may contain many more.

## Current Rule

Do not convert one-arm ORR/proportion rows to D.

Rows can enter only if the project adopts a documented conversion and minimum source-field standard.

## Research Targets

Find:

- accepted transformations from one-arm proportions to standardized mean difference or a comparable D-like scale;
- whether transformations require a comparator/control rate, null benchmark, baseline rate, variance stabilizing transformation, or event count;
- examples in meta-analysis methods literature;
- cautions about mixing one-arm response endpoints with two-arm treatment contrasts;
- recommended minimum source fields.

Suggested queries:

- `"single-arm" proportion "standardized mean difference" conversion`
- `"objective response rate" "Cohen's d" conversion`
- `"proportion" "Cohen's h" "standardized mean difference"`
- `"Chinn" odds ratio "standardized mean difference" one arm`
- `"arcsine transformation" proportion "effect size" single arm`

## Decision Criteria

Strong yes if literature supports a conversion using fields we can reliably extract, such as:

- responders and total N on both original and follow-up sides;
- same endpoint definition;
- explicit null/control/reference rate; and
- documented formula producing a D-like value comparable enough for a separate clinical lane.

Likely no if:

- conversion depends on arbitrary reference rates;
- one-arm ORR is not a treatment contrast;
- the resulting value is not comparable to D from two-arm contrasts;
- source fields are usually incomplete.

## Output

Return JSON only using this schema:

```json
{
  "task_id": "agent_file_acquisition_007",
  "verdict": "conversion_supported | conversion_supported_only_with_separate_lane | conversion_not_supported | unclear",
  "confidence": "low | medium | high",
  "method_sources": [
    {
      "url": "...",
      "citation": "...",
      "relevant_method": "...",
      "formula_or_rule": "...",
      "quoted_or_paraphrased_support": "..."
    }
  ],
  "minimum_required_fields": ["..."],
  "risks_or_cautions": ["..."],
  "recommendation_for_current_project": "...",
  "would_change_existing_rows": {
    "clinical_highly_cited_orr_rows": "include | keep_excluded | stage_native_only | unclear",
    "notes": "..."
  }
}
```

