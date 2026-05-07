# Figure 1 Individual Replication Vast Search Execution - Batch 001

- Run ID: `2026-05-05_individual_replication_vast_search_batch001`
- Query calls logged: 54
- Query calls with API errors: 12
- Raw hits screened: 322
- Relation-scored candidate units emitted: 67
- Recall probe surface checks passed: 21/38

## Route Counts

- `coverage_only`: 67

## Surface Hit Counts

- `crossref`: 120
- `europepmc`: 96
- `openalex`: 106

## Query Surface Counts

- `crossref`: 15
- `europepmc`: 12
- `openalex`: 15
- `plos`: 12

## API Errors

- `plos` `02_open_full_text_value_language_pmc_plos_europepmc_full_text__direct_re_0016__plos`: HTTPError: 510 Server Error: Not Extended for url: https://api.plos.org/search?q=%22direct+replication%22+%22Cohen%27s+d%22+%22original+study%22+%22N+%3D%22&fl=id%2Ctitle%2Cabstract%2Cauthor_display%2Cjournal%2Cpublication_date&rows=8&wt=json
- `plos` `02_open_full_text_value_language_pmc_plos_europepmc_full_text__effect_si_0017__plos`: HTTPError: 510 Server Error: Not Extended for url: https://api.plos.org/search?q=%22effect+size%22+%22replication%22+%22original%22+%22sample+size%22&fl=id%2Ctitle%2Cabstract%2Cauthor_display%2Cjournal%2Cpublication_date&rows=8&wt=json
- `plos` `02_open_full_text_value_language_pmc_plos_europepmc_full_text__means_and_0018__plos`: HTTPError: 510 Server Error: Not Extended for url: https://api.plos.org/search?q=%22means+and+standard+deviations%22+%22direct+replication%22+%22original%22&fl=id%2Ctitle%2Cabstract%2Cauthor_display%2Cjournal%2Cpublication_date&rows=8&wt=json
- `plos` `02_open_full_text_value_language_pmc_plos_europepmc_full_text__forest_pl_0019__plos`: HTTPError: 510 Server Error: Not Extended for url: https://api.plos.org/search?q=%22forest+plot%22+%22original+study%22+%22replication%22+%22Cohen%27s+d%22&fl=id%2Ctitle%2Cabstract%2Cauthor_display%2Cjournal%2Cpublication_date&rows=8&wt=json
- `plos` `02_open_full_text_value_language_pmc_plos_europepmc_full_text__original__0020__plos`: HTTPError: 510 Server Error: Not Extended for url: https://api.plos.org/search?q=%22original+effect+size%22+%22replication+effect+size%22+%22sample+size%22&fl=id%2Ctitle%2Cabstract%2Cauthor_display%2Cjournal%2Cpublication_date&rows=8&wt=json
- `plos` `02_open_full_text_value_language_pmc_plos_europepmc_full_text__original__0021__plos`: HTTPError: 510 Server Error: Not Extended for url: https://api.plos.org/search?q=%22original+study%22+%22replication+study%22+%22d+%3D%22&fl=id%2Ctitle%2Cabstract%2Cauthor_display%2Cjournal%2Cpublication_date&rows=8&wt=json
- `plos` `02_open_full_text_value_language_pmc_plos_europepmc_full_text__we_replic_0022__plos`: HTTPError: 510 Server Error: Not Extended for url: https://api.plos.org/search?q=%22we+replicated%22+%22original%22+%22Cohen%27s+d%22+%22participants%22&fl=id%2Ctitle%2Cabstract%2Cauthor_display%2Cjournal%2Cpublication_date&rows=8&wt=json
- `plos` `02_open_full_text_value_language_pmc_plos_europepmc_full_text__larger_sa_0023__plos`: HTTPError: 510 Server Error: Not Extended for url: https://api.plos.org/search?q=%22larger+sample%22+%22failed+to+replicate%22+%22Cohen%27s+d%22&fl=id%2Ctitle%2Cabstract%2Cauthor_display%2Cjournal%2Cpublication_date&rows=8&wt=json
- `plos` `02_open_full_text_value_language_pmc_plos_europepmc_full_text__event_cou_0024__plos`: HTTPError: 510 Server Error: Not Extended for url: https://api.plos.org/search?q=%22event+counts%22+%22original%22+%22replication%22+%22odds+ratio%22&fl=id%2Ctitle%2Cabstract%2Cauthor_display%2Cjournal%2Cpublication_date&rows=8&wt=json
- `plos` `02_open_full_text_value_language_pmc_plos_europepmc_full_text__2x2___rep_0025__plos`: HTTPError: 510 Server Error: Not Extended for url: https://api.plos.org/search?q=%222x2%22+%22replication%22+%22sample+size%22+%22original%22&fl=id%2Ctitle%2Cabstract%2Cauthor_display%2Cjournal%2Cpublication_date&rows=8&wt=json
- `plos` `02_open_full_text_value_language_pmc_plos_europepmc_full_text__table_1___0026__plos`: HTTPError: 510 Server Error: Not Extended for url: https://api.plos.org/search?q=%22Table+1%22+%22original%22+%22replication%22+%22Cohen%27s+d%22&fl=id%2Ctitle%2Cabstract%2Cauthor_display%2Cjournal%2Cpublication_date&rows=8&wt=json
- `plos` `02_open_full_text_value_language_pmc_plos_europepmc_full_text__sample_si_0027__plos`: HTTPError: 510 Server Error: Not Extended for url: https://api.plos.org/search?q=%22sample+size%22+%22original%22+%22replication%22+%22validation+cohort%22&fl=id%2Ctitle%2Cabstract%2Cauthor_display%2Cjournal%2Cpublication_date&rows=8&wt=json

## Outputs

- Query log: `steps/searches/figure1/individualrepsearch-query-log-batch001.tsv`
- Screened hits: `steps/searches/figure1/individualrepsearch-screening-hits-batch001.tsv`
- Recall probe results: `steps/searches/figure1/individualrepsearch-recall-probe-results-batch001.tsv`
- Candidate manifest: `steps/searches/figure1/individualrepsearch-api-batch001.json`
- Raw API responses: `steps/searches/figure1/individualrepsearch_api_batch001/raw/`

## Interpretation

This first execution is a metadata/API pass. It establishes relation-candidate discovery and recall logging, but it does not by itself verify values from local source bytes. Candidates emitted here should be resolved to original targets and full text/source objects before any row promotion.
