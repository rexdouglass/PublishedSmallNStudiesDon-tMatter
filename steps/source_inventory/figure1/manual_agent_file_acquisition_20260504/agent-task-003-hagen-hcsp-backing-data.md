# Agent Task 003: Hagen Cumulative Science Project Backing Data

## Objective

Recover the backing data for the Hagen Cumulative Science Project I Shiny app or any archived/exported master dataset with original and replication effect sizes and sample sizes.

The local project mirrored GitHub/Shiny materials, but the Google Sheets backing route returns gone/410.

## Known Routes

- OSF master project: `https://osf.io/d7za8/`
- GitHub repository: `https://github.com/pandorica-opens/Hagen-Cumulative-Science-Project-I`
- Project label: "Hagen Cumulative Science Project I"
- Domain: judgment and decision making replications.

## Search Targets

Prioritize:

- repository history for removed data URLs;
- Shiny app code that names Google Sheet IDs or CSV endpoints;
- Wayback snapshots of those Google Sheets or Shiny endpoints;
- OSF file inventories and child-project files;
- downloadable RData/RDS/CSV/XLSX backing files;
- author-maintained mirrors.

Suggested queries:

- `"Hagen Cumulative Science Project I" GitHub data`
- `"pandorica-opens" "Hagen-Cumulative-Science-Project-I" csv`
- `"Hagen Cumulative Science Project" "Google Sheets"`
- `"Hagen Cumulative Science Project" "effect size" "N"`
- `"site:osf.io d7za8 Hagen Cumulative Science Project data"`

## Pass Criteria

Strong pass if you find a file with:

- original study label or citation;
- replication study label or thesis/project identifier;
- original effect estimate;
- replication effect estimate;
- original N;
- replication N.

Partial pass if you find:

- a Google Sheet ID with archived snapshots;
- app data with effects but missing N;
- OSF child project list plus a master metadata table.

Fail if:

- only the Shiny UI is recoverable;
- child project pages exist but no master or backing data can be found;
- only a slide deck or narrative summary is found.

## Output

Return JSON only using this schema:

```json
{
  "task_id": "agent_file_acquisition_003",
  "verdict": "found_public_file | found_archived_file | found_metadata_only | found_restricted_or_request_only | not_found | not_relevant",
  "confidence": "low | medium | high",
  "found_files": [
    {
      "url": "...",
      "direct_download_url": "...",
      "file_name": "...",
      "file_format": "csv | xlsx | rds | rdata | zip | html | other",
      "source_page_url": "...",
      "access_status": "public_direct_download | archived_snapshot | browser_click_needed | login_or_request_only | unknown",
      "fields_or_columns_seen": ["..."],
      "evidence_text": "...",
      "why_relevant": "..."
    }
  ],
  "nonworking_or_blocked_routes": [
    {
      "url": "...",
      "status_or_blocker": "410 | 404 | private_google_sheet | login | metadata only | other",
      "notes": "..."
    }
  ],
  "dn_assessment": {
    "has_original_effect": "yes | no | unclear",
    "has_replication_or_followup_effect": "yes | no | unclear",
    "has_original_n": "yes | no | unclear",
    "has_replication_or_followup_n": "yes | no | unclear",
    "effect_metric": "...",
    "row_grain": "replication | effect | study | unknown",
    "notes": "..."
  },
  "recommended_next_action": "..."
}
```

