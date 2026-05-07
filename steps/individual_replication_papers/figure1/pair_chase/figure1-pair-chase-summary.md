# Figure 1 Pair-Chase Worklist

This artifact enumerates every root Figure 1 D/N pair row as an individual source-object chase or no-repull dedupe task. It does not promote or edit root rows.

- Pair rows: 2,447
- Included in current Figure 1 rule: 1,695
- Excluded by current Figure 1 rule but retained for dedupe: 752
- Side target rows: 4,894
- Original DOI present: 1,376
- Replication/follow-up DOI present: 1,133
- Both-side DOI present: 950
- Neither-side DOI present: 888
- First bounded batch size: 150 pair tasks

## Priority Meaning

- P0: existing value-bearing text can be promoted to `source_result`/`source_result_support` before new searching.
- P1: existing strict side rows or mirrored objects need alignment/parsing.
- P2: both original and replication/follow-up DOIs are available for source-object acquisition.
- P3: one side has a DOI; title-search the missing side.
- P4: no DOI in the Figure 1 table; search by title pair.
- P5: weak bibliographic identity; backfill from the source family before individual source-object acquisition.
- P6: excluded pair with at least one DOI; keep identity mapped and defer value/source chase.
- P7: excluded pair with weak or title-only identity; keep as no-repull dedupe/background target.

### Current Plot Rule Status Counts

| value | rows |
| --- | ---: |
| included_by_current_figure1_dn_rule | 1695 |
| excluded_by_current_figure1_dn_rule | 752 |

### Pair Priority Counts

| value | rows |
| --- | ---: |
| P2 | 708 |
| P4 | 503 |
| P6 | 429 |
| P3 | 422 |
| P7 | 239 |
| P0 | 138 |
| P1 | 7 |
| P5 | 1 |

### Pair Route Counts

| value | rows |
| --- | ---: |
| acquire_original_and_replication_source_objects_by_doi | 708 |
| title_pair_search_then_acquire_source_objects | 503 |
| excluded_pair_identity_map_and_deferred_source_chase | 429 |
| acquire_known_doi_side_then_title_search_missing_side | 422 |
| excluded_pair_title_or_family_identity_backfill | 239 |
| promote_existing_value_text_to_source_result | 138 |
| align_existing_side_rows_and_parse_mirrored_object | 7 |
| source_family_backfill_before_individual_chase | 1 |

### Side Source-Object Route Counts

| value | rows |
| --- | ---: |
| doi_source_object_acquisition | 2658 |
| title_source_object_search | 1854 |
| existing_value_text_promotion | 276 |
| url_source_object_acquisition | 96 |
| source_family_identifier_backfill | 10 |

### Top Source Families

| source_family_key | pair rows |
| --- | ---: |
| fred_other_additions | 504 |
| score | 282 |
| other_direct_replications | 233 |
| rpcb | 118 |
| loopr | 118 |
| student_replication_projects | 114 |
| repeat_real_world_evidence_reproductions | 106 |
| osc_2015 | 104 |
| fred_core | 85 |
| fred_sosci_submissions | 84 |
| fred_openmkt | 82 |
| fred_curatescience | 74 |
| coppock_2019_generalizability_corpus | 50 |
| registered_replication_reports | 46 |
| brazilian_reproducibility_initiative | 45 |
| sensory_marketing_replications | 38 |
| eprp | 35 |
| clinical_phase_ii_to_phase_iii_pairs | 32 |
| 251_rescue_projects | 30 |
| many_labs_2 | 28 |
| management_science_replication_project | 26 |
| decision_market_replication_project | 26 |
| eerp | 25 |
| ssrp | 23 |
| many_labs_5 | 20 |
| sports_science_replications | 19 |
| transparent_replications_by_clearer_thinking | 18 |
| experimental_asset_market_replications | 14 |
| many_labs_1 | 13 |
| fred_forrt | 11 |
