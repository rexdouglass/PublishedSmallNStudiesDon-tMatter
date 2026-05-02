# Figure 1 Codex Queue Handoff, 2026-05-02

This is the durable handoff point after the interrupted Codex session that was clearing the Figure 1 result-artifact Codex queue.

## Saved State

- The checkout was on `main`, ahead of `origin/main` by 32 commits before this checkpoint commit.
- The interrupted session had written the current Figure 1 Codex followup state at `2026-05-02 09:52`.
- The decision builder had classified 139 Codex followup rows:
  - 121 rows do not need GPT.
  - 18 rows were deterministic repair exhaustions assigned to GPT.
  - 8 rows remain assigned to Codex.

Primary files:

- `steps/source_inventory/figure1/result_artifact_acquisition/followup/codex/figure1-result-artifact-codex-decisions.tsv`
- `steps/source_inventory/figure1/result_artifact_acquisition/followup/codex/figure1-result-artifact-codex-decisions.json`
- `steps/source_inventory/figure1/result_artifact_acquisition/followup/codex/figure1-result-artifact-codex-decisions-summary.tsv`
- `steps/source_inventory/figure1/result_artifact_acquisition/followup/codex/figure1-result-artifact-codex-active-queue.tsv`
- `steps/source_inventory/figure1/result_artifact_acquisition/followup/codex/figure1-result-artifact-codex-gpt-queue.tsv`
- `steps/source_inventory/figure1/result_artifact_acquisition/followup/codex/codex_exhausted_gpt/figure1-result-artifact-codex-exhausted-gpt-batch001.json`
- `steps/source_inventory/figure1/result_artifact_acquisition/followup/codex/codex_exhausted_gpt/figure1-result-artifact-codex-exhausted-gpt-batch001-prompt.md`

The pasted GPT response in chat was malformed Markdown/JSON and was not applied as a validated decision artifact in this checkpoint.

## Active Codex Rows

All 8 active rows have decision `local_source_specific_mapping_needed` and should be cleared by inspecting local samples/files and writing a source-specific mapping or parser decision.

| followup_id | corpus_database_id | name |
| --- | --- | --- |
| `result_artifact_followup_d55e71bdfef18769` | `biblio_search_crossref_480bdd504b25` | A large-scale replication of scenario-based experiments in psychology and management using large language models |
| `result_artifact_followup_376f815512e69837` | `repo_search_datacite_1afe2afc30e4` | Circadian typology is related to resilience and optimism in healthy adults |
| `result_artifact_followup_7bb51bfa88f9a17f` | `repo_search_osf_2b928c9c5eb3` | Original Study |
| `result_artifact_followup_a7f4073b1930038b` | `repo_search_osf_92e639ac2dc7` | S23-1 many lab replication |
| `result_artifact_followup_776d4bd553ba86e2` | `repo_search_dataverse_e6b5cf171269` | Stanford Data |
| `result_artifact_followup_fb0efbbada68a67c` | `repo_search_osf_2584049b16b9` | Undergraduate Replication Projects |
| `result_artifact_followup_89f86c9b08b2c0b6` | `corpus_db_lead_marcus_four_lab_replication_hcmv7` | Marcus Four Lab Replication Hcmv7 |
| `result_artifact_followup_99820fa1dfa2fea6` | `lead_wood_porter_2019` | Wood and Porter elusive backfire effect |

## GPT Escalation Rows

The 18 GPT rows are deterministic provider/direct repair exhaustions, materialized as:

- `steps/source_inventory/figure1/result_artifact_acquisition/followup/codex/figure1-result-artifact-codex-gpt-queue.tsv`
- `steps/source_inventory/figure1/result_artifact_acquisition/followup/codex/codex_exhausted_gpt/figure1-result-artifact-codex-exhausted-gpt-batch001.json`
- `steps/source_inventory/figure1/result_artifact_acquisition/followup/codex/codex_exhausted_gpt/figure1-result-artifact-codex-exhausted-gpt-batch001-prompt.md`

The queue includes Olson/Fazio RRR aliases, Management Science Reproducibility Project, Mastroianni 2023 replication, management-journals replication census, RPP aliases, Mullinix 2015, and several no-public-artifact OSF/DataCite leads.

## Resume Commands

Regenerate the Codex queue summary:

```sh
make figure1-result-artifact-codex-decisions
```

After resolving active local mappings, regenerate local proposals and parser queues:

```sh
make figure1-result-artifact-codex-local-proposals
make figure1-result-artifact-codex-local-mirror-sample
make figure1-result-artifact-codex-local-parser-queue
make figure1-codex-local-corpus-results-extract
make figure1-codex-local-high-inspect-extract
```

If GPT decisions are returned, save them as a clean JSON artifact first, validate that every row has a known `followup_id`, and only then apply them to downstream receipt/proposal files.
