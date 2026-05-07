# Agent Task 005: RCT-DUPLICATE N Recovery

## Objective

Find files or supplements that provide original RCT sample sizes and RWE emulation cohort sample sizes for RCT-DUPLICATE, in a way that can be joined to the public result estimates.

The local project mirrored public GitHub CSVs, but they lack clean original/RWE N columns.

## Known Routes

- GitHub repository: `https://github.com/CharlotteMicheloud/RWE`
- Public raw files already mirrored locally:
  - `https://raw.githubusercontent.com/CharlotteMicheloud/RWE/main/data/all_trials_results.csv`
  - `https://raw.githubusercontent.com/CharlotteMicheloud/RWE/main/data/all_trials_results_corrected.csv`
  - `https://raw.githubusercontent.com/CharlotteMicheloud/RWE/main/data/all_trials_covariates.csv`
  - `https://raw.githubusercontent.com/CharlotteMicheloud/RWE/main/data/margins.csv`
- Article title phrase: "Assessing the replicability of RCTs in RWE emulations"

## Search Targets

Prioritize:

- supplementary tables for the RCT-DUPLICATE project;
- trial-level result tables with N;
- code that joins N into final figures;
- data dictionaries;
- appendices listing RCT trial N and RWE cohort N;
- any OHDSI/RCT-DUPLICATE repository files not under the current GitHub data folder.

Suggested queries:

- `"RCT-DUPLICATE" sample size`
- `"RCT-DUPLICATE" supplementary data`
- `"CharlotteMicheloud" "all_trials_results" "sample"`
- `"Assessing the replicability of RCTs in RWE emulations" data`
- `"RCT-DUPLICATE" "cohort size"`

## Pass Criteria

Strong pass if you find a row-level file that can join to `all_trials_results.csv` and contains:

- trial identifier;
- original RCT N or per-arm N;
- RWE/emulation N or per-arm N;
- effect estimate or enough keys to join to the public effect estimate.

Partial pass if:

- original RCT N is recoverable but RWE N is not;
- RWE N is recoverable but original RCT N is not;
- N appears only in PDF supplementary tables.

Fail if:

- public files only contain effect strings, covariates, or margins with no N;
- only article-level total counts are available.

## Output

Return JSON only using this schema:

```json
{
  "task_id": "agent_file_acquisition_005",
  "verdict": "found_public_file | found_metadata_only | found_restricted_or_request_only | not_found | not_relevant",
  "confidence": "low | medium | high",
  "found_files": [
    {
      "url": "...",
      "direct_download_url": "...",
      "file_name": "...",
      "file_format": "csv | xlsx | zip | pdf | html | other",
      "source_page_url": "...",
      "access_status": "public_direct_download | browser_click_needed | login_or_request_only | unknown",
      "fields_or_columns_seen": ["..."],
      "evidence_text": "...",
      "why_relevant": "..."
    }
  ],
  "join_keys": ["..."],
  "dn_assessment": {
    "has_original_effect": "yes | no | unclear",
    "has_replication_or_followup_effect": "yes | no | unclear",
    "has_original_n": "yes | no | unclear",
    "has_replication_or_followup_n": "yes | no | unclear",
    "effect_metric": "HR | OR | RR | other | unclear",
    "row_grain": "trial | outcome | contrast | unknown",
    "notes": "..."
  },
  "recommended_next_action": "..."
}
```

