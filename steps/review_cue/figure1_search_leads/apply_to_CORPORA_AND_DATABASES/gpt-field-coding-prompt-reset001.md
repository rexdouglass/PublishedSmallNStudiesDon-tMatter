# GPT Field-Coding Prompt: figure1_search_leads

You are coding rows for `CORPORA_AND_DATABASES.tsv` in a provenance pipeline.
Use web research only to support the requested fields. Do not invent file contents, row counts, column names, or parser status.
If a field requires artifact/file inspection rather than surface metadata, set it to `unknown` and say what must be inspected next.

Return JSON only. The user will save it as `steps/review_cue/figure1_search_leads/apply_to_CORPORA_AND_DATABASES/gpt-field-coding-response-reset001.json`.

JSON shape:

```json
{
  "field_coding_decisions": [
    {
      "coding_task_id": "...",
      "lead_key": "...",
      "field_values": {
        "source_family": "...",
        "domain_or_field": "...",
        "description": "...",
        "why_relevant": "...",
        "result_fields_available": "...",
        "has_d_or_convertible_effect": "...",
        "has_n": "...",
        "has_replication_pair_mapping": "...",
        "has_publication_links": "...",
        "parser_family": "...",
        "blocker_codes": "...",
        "next_action": "...",
        "notes": "..."
      },
      "field_basis": {
        "source_family": "short evidence basis or unknown rationale",
        "domain_or_field": "short evidence basis or unknown rationale",
        "description": "short evidence basis or unknown rationale",
        "why_relevant": "short evidence basis or unknown rationale",
        "result_fields_available": "short evidence basis or unknown rationale",
        "has_d_or_convertible_effect": "short evidence basis or unknown rationale",
        "has_n": "short evidence basis or unknown rationale",
        "has_replication_pair_mapping": "short evidence basis or unknown rationale",
        "has_publication_links": "short evidence basis or unknown rationale",
        "parser_family": "short evidence basis or unknown rationale",
        "blocker_codes": "short evidence basis or unknown rationale",
        "next_action": "short evidence basis or unknown rationale",
        "notes": "short evidence basis or unknown rationale"
      },
      "field_confidence": {
        "source_family": "high|medium|low",
        "domain_or_field": "high|medium|low",
        "description": "high|medium|low",
        "why_relevant": "high|medium|low",
        "result_fields_available": "high|medium|low",
        "has_d_or_convertible_effect": "high|medium|low",
        "has_n": "high|medium|low",
        "has_replication_pair_mapping": "high|medium|low",
        "has_publication_links": "high|medium|low",
        "parser_family": "high|medium|low",
        "blocker_codes": "high|medium|low",
        "next_action": "high|medium|low",
        "notes": "high|medium|low"
      },
      "sources_checked": [
        "URL or file path"
      ]
    }
  ]
}
```

Allowed yes/no fields must use `yes`, `no`, or `unknown`: `has_d_or_convertible_effect`, `has_n`, `has_replication_pair_mapping`, `has_publication_links`.

Rows to code:

## 1. Reproducibility Project - Psychology: Design
- coding_task_id: `fieldcode_title_reproducibility_project_psychology_design`
- lead_key: `title:reproducibility_project_psychology_design`
- landing_url: `https://osf.io/i68pe/`
- source_key: `i68pe | osf:i68pe`
- fields_to_code: `domain_or_field | description | why_relevant | has_d_or_convertible_effect | has_n | has_replication_pair_mapping | has_publication_links | parser_family`

Evidence packet:

```json
{
  "current_description": "",
  "current_notes": "provider=osf | external_id=i68pe | doi= | review_cue=figure1_search_leads | decision=keep_in_corpora_and_databases | confidence=high | reason=This is a real Reproducibility Project: Psychology OSF project/source-family lead. It belongs in the root corpus/database inventory because it can expose multiple original/replication pair rows after file-level inventory.",
  "current_why_relevant": "Matched Figure 1 repository search query '\"Reproducibility Project\" coded data'; lead_classification=corpus_database_or_project_signal; score=5; reasons=strong_phrase:reproducibility project",
  "decision": "keep_in_corpora_and_databases",
  "landing_url": "https://osf.io/i68pe/",
  "lead_key": "title:reproducibility_project_psychology_design",
  "name": "Reproducibility Project - Psychology: Design",
  "proposal_basis": "This is a real Reproducibility Project: Psychology OSF project/source-family lead. It belongs in the root corpus/database inventory because it can expose multiple original/replication pair rows after file-level inventory.",
  "source_key": "i68pe | osf:i68pe"
}
```
