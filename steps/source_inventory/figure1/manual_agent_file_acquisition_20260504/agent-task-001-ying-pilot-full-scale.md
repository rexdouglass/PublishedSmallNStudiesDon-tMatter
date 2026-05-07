# Agent Task 001: Ying/Ehrhardt Pilot-To-Full-Scale Treatment-Effect Dataset

## Objective

Find a public or requestable row-level dataset for Ying/Ehrhardt pilot-to-full-scale clinical trials that contains treatment-effect estimates and sample sizes for both the pilot/original trial and the later full-scale trial.

This is not a bibliography task. We need exact files, direct download URLs, supplements, repository records, or clear evidence that the row-level file is request-only.

## Why This Matters

The local project has only 5 included Ying-family rows, but the research lead suggests a much larger roster, roughly 248 pilot/full-scale trial pairs. If the analytic treatment-effect dataset is available, it may be the largest remaining source of Figure 1 rows.

## Known Identifiers And Routes

- BMJ EBM article DOI: `10.1136/bmjebm-2023-112358`
- JHU dissertation record: "Role of Pilot Trials in RCT Quality and Feasibility"
- JAMA Network Open article DOI: `10.1001/jamanetworkopen.2023.33642`
- Known local blocker: our automated routes were blocked or landing-only; no public D/N master table was mirrored.

## Search Targets

Prioritize:

- supplementary files;
- data availability statements;
- JHU repository attachments;
- author-shared OSF/GitHub/Dataverse/figshare/Zenodo records;
- Excel/CSV/SAV/RDS/stata files;
- appendices that list pair-level effect estimates and sample sizes.

Suggested queries:

- `"10.1136/bmjebm-2023-112358" supplement data`
- `"Role of Pilot Trials in RCT Quality and Feasibility" dataset`
- `"pilot full-scale trial pairs" Ying Ehrhardt data`
- `"bmjebm-2023-112358" "data available"`
- `"10.1001/jamanetworkopen.2023.33642" supplement dataset`

## Pass Criteria

Strong pass if you find a file with row-level columns like:

- pilot/original DOI, citation, or trial identifier;
- full-scale/follow-up DOI, citation, or trial identifier;
- pilot/original sample size;
- full-scale/follow-up sample size;
- treatment-effect estimate, confidence interval, standard error, p-value, event counts, means/SDs, OR/RR/HR, or another convertible metric for both sides.

Partial pass if you find:

- the 248-pair roster plus enough source article links to reconstruct rows manually;
- request-only data contact or exact repository record proving the analytic file exists.

Fail if you only find:

- article landing pages;
- abstracts;
- narrative statements about agreement without row-level values;
- feasibility outcomes only, unless clearly linked to a treatment-effect dataset.

## Output

Return JSON only using this schema:

```json
{
  "task_id": "agent_file_acquisition_001",
  "verdict": "found_public_file | found_metadata_only | found_restricted_or_request_only | not_found | not_relevant",
  "confidence": "low | medium | high",
  "found_files": [
    {
      "url": "...",
      "direct_download_url": "...",
      "file_name": "...",
      "file_format": "csv | xlsx | sav | rds | dta | zip | pdf | html | other",
      "source_page_url": "...",
      "access_status": "public_direct_download | browser_click_needed | login_or_request_only | paywalled | unknown",
      "fields_or_columns_seen": ["..."],
      "evidence_text": "...",
      "why_relevant": "..."
    }
  ],
  "nonworking_or_blocked_routes": [
    {
      "url": "...",
      "status_or_blocker": "403 | 404 | login | no supplement | metadata only | request-only | other",
      "notes": "..."
    }
  ],
  "dn_assessment": {
    "has_original_effect": "yes | no | unclear",
    "has_replication_or_followup_effect": "yes | no | unclear",
    "has_original_n": "yes | no | unclear",
    "has_replication_or_followup_n": "yes | no | unclear",
    "effect_metric": "...",
    "row_grain": "trial-pair | effect | outcome | unknown",
    "notes": "..."
  },
  "recommended_next_action": "..."
}
```

