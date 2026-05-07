# Agent Task 004: FORRT Replications & Reversals Export And Dedupe Files

## Objective

Find a machine-readable export for FORRT Replications & Reversals and the latest FReD/Replication Database export, then determine whether the current conservative FORRT Reversals candidates are already represented in FReD or likely new.

This is partly a file acquisition task and partly a dedupe task.

## Known Local Finding

The local HTML mirror at `https://forrt.org/reversals/` contains narrative entries. A conservative parser found 10 D/N-like entries, 8 with larger replication N:

- Fluency priming
- Sex differences in implicit maths attitudes
- Door-in-the-face effect
- Left-cradling bias
- Handedness differences in schizophrenia
- Eye movements and false memories
- Conjunction bias
- Right-bias in chimpanzee hand use

These were not promoted because overlap with FReD/current rows is likely.

## Search Targets

Prioritize:

- FORRT Reversals CSV/JSON/export source;
- GitHub source for the FORRT Reversals table;
- latest FReD XLSX/CSV export;
- OSF records behind FReD;
- row labels or IDs that match the 8 candidates above.

Known useful routes:

- `https://forrt.org/reversals/`
- `https://forrt.org/replication-database/`
- `https://osf.io/9r62x/`
- `https://osf.io/z5u9b/`
- `https://github.com/forrtproject/FReD`

## Pass Criteria

Strong pass if you find:

- a direct machine-readable FORRT Reversals export; and
- FReD row IDs or table rows matching each of the 8 candidate labels; or
- evidence that a candidate is absent from FReD and has clear original/replication D/N values.

Partial pass if:

- only FReD export is found;
- only FORRT HTML is found but row details are clearer than the current page;
- candidate duplicates are identified by title/effect/N without row IDs.

Fail if:

- no machine-readable export exists and no dedupe evidence can be established.

## Output

Return JSON only using this schema:

```json
{
  "task_id": "agent_file_acquisition_004",
  "verdict": "found_public_file | found_html_only | found_metadata_only | not_found | not_relevant",
  "confidence": "low | medium | high",
  "found_files": [
    {
      "url": "...",
      "direct_download_url": "...",
      "file_name": "...",
      "file_format": "csv | xlsx | json | html | other",
      "source_page_url": "...",
      "access_status": "public_direct_download | browser_click_needed | unknown",
      "fields_or_columns_seen": ["..."],
      "evidence_text": "...",
      "why_relevant": "..."
    }
  ],
  "candidate_dedupe": [
    {
      "candidate_label": "...",
      "likely_in_fred": "yes | no | unclear",
      "matching_fred_row_or_source": "...",
      "original_n": "...",
      "replication_n": "...",
      "original_effect": "...",
      "replication_effect": "...",
      "notes": "..."
    }
  ],
  "dn_assessment": {
    "has_original_effect": "yes | no | unclear",
    "has_replication_or_followup_effect": "yes | no | unclear",
    "has_original_n": "yes | no | unclear",
    "has_replication_or_followup_n": "yes | no | unclear",
    "effect_metric": "d | r | other | unclear",
    "row_grain": "phenomenon | study-pair | effect | unknown",
    "notes": "..."
  },
  "recommended_next_action": "..."
}
```

