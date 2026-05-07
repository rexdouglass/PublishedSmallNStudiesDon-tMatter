# Figure 1 Individual Replication Vast Search Execution - batch006

- Run ID: `2026-05-05_individual_replication_vast_search_batch006`
- Query calls logged: 181
- Query calls with API errors: 0
- Raw hits screened: 4,008
- Relation-scored candidate units emitted: 459
- Recall probe surface checks passed: 0/0

## Route Counts

- `coverage_only`: 458
- `strict_figure1a`: 1

## Surface Hit Counts

- `crossref`: 1,560
- `datacite`: 56
- `europepmc`: 988
- `openalex`: 1,074
- `plos`: 330

## Query Surface Counts

- `crossref`: 52
- `datacite`: 18
- `europepmc`: 50
- `openalex`: 49
- `plos`: 12

## Outputs

- Query log: `steps/searches/figure1/individualrepsearch-query-log-batch006.tsv`
- Screened hits: `steps/searches/figure1/individualrepsearch-screening-hits-batch006.tsv`
- Recall probe results: `steps/searches/figure1/individualrepsearch-recall-probe-results-batch006.tsv`
- Candidate manifest: `steps/searches/figure1/individualrepsearch-api-batch006.json`
- Raw API responses: `steps/searches/figure1/individualrepsearch_api_batch006/raw/`

## Interpretation

This first execution is a metadata/API pass. It establishes relation-candidate discovery and recall logging, but it does not by itself verify values from local source bytes. Candidates emitted here should be resolved to original targets and full text/source objects before any row promotion.
