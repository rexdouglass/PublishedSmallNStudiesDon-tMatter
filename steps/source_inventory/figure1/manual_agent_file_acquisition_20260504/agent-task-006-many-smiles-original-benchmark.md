# Agent Task 006: Many Smiles Original Benchmark Effect/N Table

## Objective

Find an exact source table for the original benchmark effect and original sample size for each Many Smiles target, so the existing replication-side data can be paired under the strict Figure 1 D/N rule.

The local blocker is not replication data. The blocker is a defensible original-side benchmark D and N at the same row grain as the replication result.

## Known Routes

- Many Smiles article DOI: `10.1038/s41562-022-01458-9`
- Project/site phrase: "Many Smiles Collaboration"
- Related benchmark likely includes Strack 1988 and/or Coles 2019 facial-feedback meta-analysis.

## Search Targets

Prioritize:

- supplementary data from the Nature Human Behaviour article;
- OSF project files linked from the paper;
- Coles 2019 meta-analysis data/code;
- tables listing original effect sizes and original sample sizes for the targeted tasks;
- lab-level or task-level mapping between replication outcomes and original benchmarks.

Suggested queries:

- `"10.1038/s41562-022-01458-9" supplementary data effect size`
- `"Many Smiles Collaboration" OSF data`
- `"Many Smiles" "original effect" "sample size"`
- `"Coles 2019" facial feedback meta-analysis data`
- `"Strack 1988" "Many Smiles" effect size`

## Pass Criteria

Strong pass if you find a table with:

- target/task label;
- original source or benchmark source;
- original effect estimate, preferably D or convertible to D;
- original N;
- replication effect and N or join key to replication-side data.

Partial pass if:

- original benchmark effects exist but N is missing;
- original N exists but effect is only in a plot;
- benchmark is meta-analytic and not single-original, but row grain is explicit.

Fail if:

- only aggregate statements are found;
- original benchmark is a meta-analysis without extractable row-level N/effect;
- source only supports a broad narrative comparison.

## Output

Return JSON only using this schema:

```json
{
  "task_id": "agent_file_acquisition_006",
  "verdict": "found_public_file | found_metadata_only | found_restricted_or_request_only | not_found | not_relevant",
  "confidence": "low | medium | high",
  "found_files": [
    {
      "url": "...",
      "direct_download_url": "...",
      "file_name": "...",
      "file_format": "csv | xlsx | rds | zip | pdf | html | other",
      "source_page_url": "...",
      "access_status": "public_direct_download | browser_click_needed | login_or_request_only | unknown",
      "fields_or_columns_seen": ["..."],
      "evidence_text": "...",
      "why_relevant": "..."
    }
  ],
  "dn_assessment": {
    "has_original_effect": "yes | no | unclear",
    "has_replication_or_followup_effect": "yes | no | unclear",
    "has_original_n": "yes | no | unclear",
    "has_replication_or_followup_n": "yes | no | unclear",
    "effect_metric": "d | mean difference | r | other | unclear",
    "row_grain": "task | lab-task | benchmark | meta-analytic benchmark | unknown",
    "notes": "..."
  },
  "recommended_next_action": "..."
}
```

