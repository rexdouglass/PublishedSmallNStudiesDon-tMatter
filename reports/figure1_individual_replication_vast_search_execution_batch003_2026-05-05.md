# Figure 1 Individual Replication Vast Search Execution - batch003

- Run ID: `2026-05-05_individual_replication_vast_search_batch003`
- Query calls logged: 96
- Query calls with API errors: 0
- Raw hits screened: 1,783
- Relation-scored candidate units emitted: 261
- Recall probe surface checks passed: 0/0

## Route Counts

- `coverage_only`: 261

## Surface Hit Counts

- `crossref`: 540
- `europepmc`: 592
- `openalex`: 422
- `plos`: 229

## Query Surface Counts

- `crossref`: 27
- `europepmc`: 33
- `openalex`: 24
- `plos`: 12

## Outputs

- Query log: `steps/searches/figure1/individualrepsearch-query-log-batch003.tsv`
- Screened hits: `steps/searches/figure1/individualrepsearch-screening-hits-batch003.tsv`
- Recall probe results: `steps/searches/figure1/individualrepsearch-recall-probe-results-batch003.tsv`
- Candidate manifest: `steps/searches/figure1/individualrepsearch-api-batch003.json`
- Raw API responses: `steps/searches/figure1/individualrepsearch_api_batch003/raw/`

## Interpretation

This first execution is a metadata/API pass. It establishes relation-candidate discovery and recall logging, but it does not by itself verify values from local source bytes. Candidates emitted here should be resolved to original targets and full text/source objects before any row promotion.
