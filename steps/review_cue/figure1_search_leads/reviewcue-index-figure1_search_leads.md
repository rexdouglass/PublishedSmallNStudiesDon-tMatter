# Review Cue: figure1_search_leads

Reusable bounded review queue for ambiguous Figure 1 corpus/database, repository-package, result-table, individual-paper, and context-source leads. Deterministic scripts should remove obvious duplicates and false positives first. Codex should investigate moderate batches and either make auditable decisions or emit compact GPT prompt requests for uncertain cases. GPT prompt batches can be larger because they are user-mediated review artifacts.

- Queue: `steps/review_cue/figure1_search_leads/reviewcue-queue-figure1_search_leads.json`
- Open items: 978
- Skip counts: `{"already_in_root_target": 13, "already_reviewed": 60, "deterministically_skipped": 49}`

Run:

```bash
python scripts/build_review_cue.py --cue-id figure1_search_leads --replace
```

Codex can work a small batch and write decisions. GPT Pro handoff prompts are generated as Markdown prompt files in this directory.
