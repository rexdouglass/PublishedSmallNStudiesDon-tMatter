# Figure 1 Individual Replication Vast Search Plan

This plan starts after the cheap corpus/database route is saturated. The goal is no longer to find another many-row dataset; it is to find individual papers that explicitly replicate, validate, retest, or definitively follow up an earlier paper/result.

## Why This Is Different From The GPT Lead Prompts

The earlier GPT prompts were seed discovery: useful for named leads, but not a measured search over literature surfaces. The vast search has to be recall-auditable. Every query family writes a manifest, every manifest runs through the same dedupe gate, and known-good probes check whether the search recovers famous paper-level replications before we interpret misses as absence.

## Unit Of Work

The candidate unit is not just a replication paper. It is:

```text
original_work x replication_work x original_study/result x replication_study/result x outcome x contrast/timepoint x aggregation_level
```

The pipeline is:

```text
raw hit -> candidate replication/follow-up paper -> resolved original target -> paper-pair candidate -> study/outcome-level pair -> value extraction -> routing label
```

Relation discovery is separate from value extraction. A paper becomes a pair candidate only after affirmative evidence says it is replicating, validating, retesting, or definitively following up a specific earlier result. Value extraction then determines strict Figure 1A, D-equivalent Figure 1B, native-only, coverage-only, or reject routing.

## Campaign Order

1. Run known-good recall probes against the query bank. If famous paper-level replications are missed, expand the phrase family before mining long-tail results.
2. Run metadata phrase searches in OpenAlex, Crossref, Semantic Scholar, PubMed, and EuropePMC. Capture titles/abstracts and DOI/PMID/PMCID IDs.
3. Run open full-text value-language searches in PMC, PLOS, and EuropePMC. Prioritize hits that expose D/statistic/N text.
4. Run repository package searches in OSF, Figshare, Dataverse, Zenodo, GitHub, and Dryad. Accept packages only when they identify a paper-level original/replication relation or source values.
5. Run citation-forward searches from known original papers and from unresolved current Figure 1 side targets. Filter citing papers for replication language.
6. Run domain lanes: psychology long tail, behavioral economics/marketing/management, education/health/sports, clinical follow-up, and genetics validation.
7. Apply negative filters for same-data reanalyses, computational-only reproductions, and review-only records.
8. Save candidates as `individualrepsearch-*.json`, then run `make figure1-individual-replication-search-intake`.

## Query Bank Summary

- `01_metadata_replication_language`: 15 queries
- `02_open_full_text_value_language`: 12 queries
- `03_repository_source_object_search`: 10 queries
- `04_psychology_long_tail`: 9 queries
- `05_behavioral_econ_marketing_management`: 8 queries
- `06_education_health_sports`: 8 queries
- `07_clinical_d_equivalent_followup`: 12 queries
- `08_genetics_validation_native`: 9 queries
- `09_citation_snowball_known_originals`: 4 queries
- `10_negative_filters_context`: 6 queries

## Promotion Gates

- Strict Figure 1A requires original D-compatible effect, original N, replication D-compatible effect, replication N, and a larger replication/follow-up N under the current rule.
- Figure 1B D-equivalent requires comparative binary inputs such as event counts, OR/logOR, RR/RD with baseline risk, and documented conversion.
- Native-only rows preserve useful paper pairs that cannot be put on the D axis.
- Coverage-only rows prove a target exists and should not be re-pulled, even if public values are missing.
- Reject same-data reanalyses, generic reviews, one-arm ORR without comparator, and ordinary citations without affirmative replication relation evidence.

Use the relation-evidence scale and routing-score rules as the screening contract:

- Design YAML: `steps/searches/figure1/individualrepsearch-design.yml`
- Relation evidence scale: `steps/searches/figure1/individualrepsearch-relation-evidence-scale.tsv`
- Routing score rules: `steps/searches/figure1/individualrepsearch-routing-score-rules.tsv`
- Query log schema: `steps/searches/figure1/individualrepsearch-query-log-schema.tsv`

## Stop Or Expand Rules

- Stop a query family only when relevant recall probes are recovered, two consecutive batches add fewer than 1-2 accepted relation candidates per 500 screened, and citation expansion from accepted pairs yields no new unique candidates.
- Expand when a recall probe is missed, a domain has many seed-only review mentions but few primary papers, repository hits reveal unsearched article titles/DOIs, or candidates use confirm/validate/retest language rather than replicate language.
- Record every query in the query log. Do not silently drop false positives; write reject reasons or coverage/native blockers so future searches can dedupe them.

## Output Artifacts

- Design YAML: `steps/searches/figure1/individualrepsearch-design.yml`
- Query bank TSV: `steps/searches/figure1/individualrepsearch-vast-query-bank.tsv`
- Known-good recall probes: `steps/searches/figure1/individualrepsearch-known-good-recall-probes.tsv`
- Relation evidence scale: `steps/searches/figure1/individualrepsearch-relation-evidence-scale.tsv`
- Routing score rules: `steps/searches/figure1/individualrepsearch-routing-score-rules.tsv`
- Query log schema: `steps/searches/figure1/individualrepsearch-query-log-schema.tsv`
- Candidate schema: `steps/searches/figure1/individualrepsearch-candidate-schema.json`
- Intake README: `steps/searches/figure1/individualrepsearch-intake-readme.md`
