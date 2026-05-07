# Batch Prompt: Figure 1 Missing File Acquisition

You are helping recover missing files for a provenance-heavy Figure 1 dataset. Figure 1 pairs original results with larger-N replication, reproduction, or follow-up results.

Do not return generic replication-project suggestions. We already did broad discovery. Your job is to find exact files or prove that exact files are not publicly accessible.

Strict Figure 1 D/N rule:

- original and replication/follow-up effects must be numeric and convertible to the same D-like axis;
- original and replication/follow-up sample sizes must both be numeric;
- both N values must be at least 10;
- the replication/follow-up N must be larger than original N.

Take the tasks below independently. For each, return JSON only using the schema below.

```json
{
  "tasks": [
    {
      "task_id": "agent_file_acquisition_001",
      "verdict": "found_public_file | found_metadata_only | found_restricted_or_request_only | not_found | not_relevant",
      "confidence": "low | medium | high",
      "found_files": [
        {
          "url": "...",
          "direct_download_url": "...",
          "file_name": "...",
          "file_format": "csv | xlsx | sav | rds | zip | pdf | html | other",
          "source_page_url": "...",
          "access_status": "downloaded_by_agent | public_direct_download | browser_click_needed | login_or_request_only | paywalled | unknown",
          "fields_or_columns_seen": ["..."],
          "evidence_text": "Short quoted or paraphrased evidence that this file contains row-level effect/N data.",
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
        "row_grain": "effect | construct | study | trial | claim | unknown",
        "notes": "..."
      },
      "recommended_next_action": "..."
    }
  ]
}
```

Tasks to run:

- `agent_file_acquisition_001`: Ying/Ehrhardt pilot-to-full-scale treatment-effect dataset.
- `agent_file_acquisition_002`: Beets/von Klinggraeff RGB health-behavior pilot-vs-larger-trial extraction workbooks.
- `agent_file_acquisition_003`: Hagen Cumulative Science Project backing data.
- `agent_file_acquisition_004`: FORRT Replications & Reversals export and dedupe files.
- `agent_file_acquisition_005`: RCT-DUPLICATE original and RWE N recovery.
- `agent_file_acquisition_006`: Many Smiles original benchmark effect/N table.
- `agent_file_acquisition_007`: Clinical one-arm ORR/proportion conversion scope.

The detailed task prompts are in the sibling `agent-task-*.md` files.

