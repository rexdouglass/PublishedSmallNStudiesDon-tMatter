# Figure 1 Prior Pair Work Reconciliation

This audit checks whether the current pair-chase/BibTeX work is duplicating an older Figure 1 pair mapping.

## Verdict

The earlier pair-detail projection has 1,548 rows. The current scripted root table has 2,436 rows: 1,684 included by the current Figure 1 D/N rule and 752 excluded but retained as no-repull/dedupe targets.

By stable pair ID, 1,548 / 1,548 old rows are present in the current table, with 0 old-only pair IDs and 888 current pair IDs not present in the old projection. So the old work was real and useful, but it was a smaller plotted-pair projection rather than the full current pair universe.

The 300-row schema pilot is also real prior work. It should be reused as the source/source_result/schema precedent, not as a complete pair registry.

## Artifact Inventory

| artifact | rows | columns | lineage | reuse decision |
| --- | ---: | ---: | --- | --- |
| `old_pair_detail_projection` | 1548 | 27 | prior work | reuse as historical subset and value/source-family clue; do not treat as full current universe |
| `current_root_pair_table` | 2436 | 48 | current scripted root | canonical staging table for pair-level worklists |
| `schema_pilot_source_result_sample` | 300 | 74 | prior schema pilot | reuse as schema precedent for source_result/source_result_support promotion |
| `schema_pilot_source_sample` | 331 | 13 | prior schema pilot | reuse as source/source mapping precedent |
| `schema_pilot_source_source_mapping_sample` | 454 | 32 | prior schema pilot | reuse as replication/source relationship precedent |
| `current_pair_chase_worklist` | 2436 | 43 | current scripted worklist | use as pair-specific source-object chase and no-repull dedupe queue |
| `current_pair_side_targets` | 4872 | 21 | current scripted worklist | use as side-level acquisition/extraction queue |
| `current_individual_study_map` | 2605 | 38 | current scripted dedupe map | use as first-pass dedupe registry for new individual replication candidates |
| `current_side_to_individual_study_map` | 4872 | 27 | current scripted dedupe map | preserves pair-side grain after deduping represented sources |
| `current_individual_study_bibtex_map` | 2605 | 21 | current scripted bibliography map | use as BibTeX-key dedupe bridge |
| `current_side_to_bibtex_map` | 4872 | 20 | current scripted bibliography map | use to test whether a proposed individual pair side is already represented |
| `current_pair_bibtex_map` | 2436 | 44 | current scripted bibliography map | use as the primary dedupe gate for new individual replication pairs |
| `current_identity_disambiguation_worklist` | 1766 | 34 | current scripted disambiguation queue | use as the next-step queue for resolving local labels to DOI/PMID/PMCID/stable citations |
| `current_identity_disambiguation_batch001` | 200 | 34 | current scripted disambiguation queue | use for the next manual/Codex/GPT grounding batch |

## Current Additions Beyond The Old Projection

| source_family_key | new-only rows |
| --- | ---: |
| other_direct_replications | 133 |
| fred_other_additions | 126 |
| score | 111 |
| repeat_real_world_evidence_reproductions | 106 |
| rpcb | 85 |
| student_replication_projects | 79 |
| sensory_marketing_replications | 38 |
| osc_2015 | 33 |
| brazilian_reproducibility_initiative | 24 |
| fred_sosci_submissions | 23 |
| registered_replication_reports | 21 |
| transparent_replications_by_clearer_thinking | 18 |
| coppock_2019_generalizability_corpus | 15 |
| loopr | 14 |
| experimental_asset_market_replications | 14 |

## Reuse Decision

- Use `FIGURE1_REPLICATION_PAIRS.tsv` as the current root pair universe.
- Use `figure1-pair-chase-worklist.tsv` for pair-level chase/no-repull tasks.
- Use `figure1-pair-bibtex-map.tsv` as the pair-level dedupe gate before chasing new individual pairs.
- Use `figure1-individual-study-map.tsv` and `figure1-individual-study-bibtex-map.tsv` as side/source identity support for that pair-level gate.
- Use `figure1-identity-disambiguation-worklist.tsv` to resolve title-only, URL-only, and weak identities to real citations before source-object chasing.
- Reuse the old `plot1_replication_pair_details.csv` as a historical subset and sanity check, not as the current registry.
- Reuse `schema_pilot/*_codebook_sample_300.tsv` as the model for future source/source_result/source_source_mapping promotion.

## Metric Rows

Machine-readable metrics: `steps/individual_replication_papers/figure1/pair_chase/figure1-prior-pair-work-reconciliation.tsv`.

