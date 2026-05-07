# Figure 1 Individual Replication Vast Search Execution - batch004

- Run ID: `2026-05-05_individual_replication_vast_search_batch004`
- Query calls logged: 96
- Query calls with API errors: 0
- Raw hits screened: 2,576
- Relation-scored candidate units emitted: 343
- Recall probe surface checks passed: 0/0

## Route Counts

- `coverage_only`: 343

## Surface Hit Counts

- `crossref`: 810
- `europepmc`: 841
- `openalex`: 595
- `plos`: 330

## Query Surface Counts

- `crossref`: 27
- `europepmc`: 33
- `openalex`: 24
- `plos`: 12

## Outputs

- Query log: `steps/searches/figure1/individualrepsearch-query-log-batch004.tsv`
- Screened hits: `steps/searches/figure1/individualrepsearch-screening-hits-batch004.tsv`
- Recall probe results: `steps/searches/figure1/individualrepsearch-recall-probe-results-batch004.tsv`
- Candidate manifest: `steps/searches/figure1/individualrepsearch-api-batch004.json`
- Raw API responses: `steps/searches/figure1/individualrepsearch_api_batch004/raw/`

## Interpretation

This first execution is a metadata/API pass. It establishes relation-candidate discovery and recall logging, but it does not by itself verify values from local source bytes. Candidates emitted here should be resolved to original targets and full text/source objects before any row promotion.
