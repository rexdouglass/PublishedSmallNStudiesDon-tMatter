# Agent Task 002: RGB Health-Behavior Pilot-Vs-Larger-Trial Extraction Workbooks

## Objective

Find the row-level extraction workbooks or datasets for the risk-of-generalizability-biases family comparing preliminary/pilot studies with larger efficacy/effectiveness trials.

The local project mirrored article/preprint pages, but did not obtain a public master D/N workbook or CSV.

## Why This Matters

This family appears strongly aligned with Figure 1: preliminary or pilot effects are compared with later larger-trial effects, often using standardized mean differences. The potential yield is substantial if the extraction tables are obtainable.

## Known Targets

Childhood obesity:

- DOI: `10.1186/s12966-020-0918-y`
- Title: "Identification and evaluation of risk of generalizability biases in pilot versus efficacy/effectiveness trials: A systematic review and meta-analysis"

Adult obesity:

- DOI: `10.1111/obr.13369`
- Cambridge repository DOI: `10.17863/CAM.78261`
- Known repository route: `https://www.repository.cam.ac.uk/handle/1810/330818`

Broader health behavior:

- PubMed: `38464006`
- Research Square DOI: `10.21203/rs.3.rs-3897976/v1`
- Title phrase: "Are the risk of generalizability biases generalizable?"

## Search Targets

Prioritize:

- supplementary Excel/CSV workbooks;
- repository attachments;
- OSF/GitHub/Dataverse/figshare/Zenodo files;
- article appendices with construct-level SMD tables;
- data availability statements that name the dataset owner/contact.

Suggested queries:

- `"10.1186/s12966-020-0918-y" supplementary data`
- `"risk of generalizability biases" pilot efficacy effectiveness trials data`
- `"10.1111/obr.13369" supplementary table`
- `"10.17863/CAM.78261" data`
- `"Are the Risk of Generalizability Biases Generalizable" supplementary`
- `"rs-3897976" data SMD`

## Pass Criteria

Strong pass if you find a file with row-level columns like:

- pilot/preliminary study identifier;
- larger efficacy/effectiveness study identifier;
- construct or outcome name;
- pilot/preliminary SMD or convertible effect;
- larger-trial SMD or convertible effect;
- pilot/preliminary N;
- larger-trial N.

Partial pass if you find:

- a workbook with effects but not N;
- a workbook with N but only native effects;
- request-only data instructions or author contact for the exact extraction table.

Fail if you only find:

- narrative article pages;
- abstract-level counts such as "39 pairs" or "156 effects";
- non-downloadable figures.

## Output

Return JSON only using this schema:

```json
{
  "task_id": "agent_file_acquisition_002",
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
    "effect_metric": "SMD | mean difference | OR | RR | other | unclear",
    "row_grain": "construct | effect | study-pair | unknown",
    "notes": "..."
  },
  "recommended_next_action": "..."
}
```

