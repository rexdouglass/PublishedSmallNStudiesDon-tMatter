# Figure 1 Individual Replication Vast Search Execution - batch002

- Run ID: `2026-05-05_individual_replication_vast_search_batch002`
- Query calls logged: 78
- Query calls with API errors: 0
- Raw hits screened: 877
- Relation-scored candidate units emitted: 122
- Recall probe surface checks passed: 21/38

## Route Counts

- `coverage_only`: 122

## Surface Hit Counts

- `crossref`: 324
- `europepmc`: 258
- `openalex`: 154
- `plos`: 141

## Query Surface Counts

- `crossref`: 27
- `europepmc`: 24
- `openalex`: 15
- `plos`: 12

## Outputs

- Query log: `steps/searches/figure1/individualrepsearch-query-log-batch002.tsv`
- Screened hits: `steps/searches/figure1/individualrepsearch-screening-hits-batch002.tsv`
- Recall probe results: `steps/searches/figure1/individualrepsearch-recall-probe-results-batch002.tsv`
- Candidate manifest: `steps/searches/figure1/individualrepsearch-api-batch002.json`
- Raw API responses: `steps/searches/figure1/individualrepsearch_api_batch002/raw/`

## Interpretation

This first execution is a metadata/API pass. It establishes relation-candidate discovery and recall logging, but it does not by itself verify values from local source bytes. Candidates emitted here should be resolved to original targets and full text/source objects before any row promotion.
