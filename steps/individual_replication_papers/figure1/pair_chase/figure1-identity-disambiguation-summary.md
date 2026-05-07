# Figure 1 Identity Disambiguation Worklist

This artifact routes title-only, URL-only, and weak represented source identities toward real citeable records before individual-pair chasing.

- Disambiguation tasks: 1,766
- Tasks touching current included Figure 1 pairs: 1,119
- First bounded batch: 200

## Priority Meaning

- D0: included weak identity; backfill from source-family artifacts first.
- D1: included title-only identity; resolve title/citation string to DOI/PMID/PMCID/stable source.
- D2: included URL-backed non-DOI identity; inspect URL and promote standard citation metadata if possible.
- D3: excluded title-only identity; retain for dedupe and resolve when cheap or colliding.
- D4: excluded weak identity; deferred backfill/no-repull target.
- D5: excluded URL-backed non-DOI identity; deferred URL citation promotion.
- D6: DOI-backed identity already grounded, but display title needs metadata cleanup.

## Priority Counts

| value | rows |
| --- | ---: |
| D1 | 1021 |
| D3 | 520 |
| D4 | 94 |
| D2 | 63 |
| D0 | 34 |
| D5 | 33 |
| D6 | 1 |

## Route Counts

| value | rows |
| --- | ---: |
| title_to_real_citation_for_included_identity | 1021 |
| title_to_real_citation_for_excluded_identity | 520 |
| deferred_source_family_backfill_for_excluded_weak_identity | 94 |
| url_to_real_citation_for_included_identity | 63 |
| source_family_backfill_for_included_weak_identity | 34 |
| deferred_url_to_real_citation_for_excluded_identity | 33 |
| doi_backed_title_metadata_cleanup | 1 |

## Dedupe Method Counts

| value | rows |
| --- | ---: |
| title | 1541 |
| weak_side_target | 128 |
| url | 96 |
| doi | 1 |

## Top Source Families

| source_family_keys | rows |
| --- | ---: |
| score | 283 |
| student_replication_projects | 228 |
| osc_2015 | 200 |
| other_direct_replications | 129 |
| rpcb | 118 |
| repeat_real_world_evidence_reproductions | 106 |
| eprp | 69 |
| clinical_phase_ii_to_phase_iii_pairs | 64 |
| many_labs_2 | 56 |
| decision_market_replication_project | 52 |
| 251_rescue_projects | 46 |
| ssrp | 45 |
| brazilian_reproducibility_initiative | 45 |
| eerp | 44 |
| registered_replication_reports | 44 |
| loopr | 35 |
| fred_other_additions | 34 |
| management_science_replication_project | 32 |
| many_labs_5 | 30 |
| coppock_2019_generalizability_corpus | 27 |
| experimental_asset_market_replications | 14 |
| many_labs_1 | 12 |
| pipeline_project | 11 |
| sensory_marketing_replications | 10 |
| many_labs_3 | 10 |
| fred_curatescience | 6 |
| transparent_replications_by_clearer_thinking | 4 |
| fred_sosci_submissions | 2 |
| fred_core | 2 |
| marek_2022_bwas | 2 |
