# Figure 1 Individual Replication Search Intake

Save GPT/Gemini/tool outputs as `steps/searches/figure1/individualrepsearch-*.json`.
Each manifest should follow `individualrepsearch-candidate-schema.json`.

Run:

```text
make figure1-individual-replication-search-intake
make figure1-individual-replication-mirror-batch001
make figure1-individual-replication-value-scan-batch001
make figure1-individual-replication-promote-ready
```

The intake step dedupes against the current Figure 1 pair/BibTeX maps before any source-object mirroring or row promotion.

For the broad paper-level campaign, start with:

```text
steps/searches/figure1/individualrepsearch-vast-run-plan.md
steps/searches/figure1/individualrepsearch-design.yml
steps/searches/figure1/individualrepsearch-vast-query-bank.tsv
steps/searches/figure1/individualrepsearch-known-good-recall-probes.tsv
steps/searches/figure1/individualrepsearch-relation-evidence-scale.tsv
steps/searches/figure1/individualrepsearch-routing-score-rules.tsv
steps/searches/figure1/individualrepsearch-query-log-schema.tsv
```

Screening grain: original_work x replication_work x original_study/result x replication_study/result x outcome x contrast/timepoint x aggregation_level.

Relation discovery is separate from value extraction. Do not route a paper into Figure 1 unless it has affirmative relation evidence under the relation scale and enough value support for the selected route.
