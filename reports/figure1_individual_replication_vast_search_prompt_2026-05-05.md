# Figure 1 Individual Replication Vast Search Prompt - 2026-05-05

Use this prompt when asking GPT/Gemini/Deep Research or a human assistant to run a systematic paper-level search after corpus/database saturation.

## Goal

Find individual paper-to-paper replication, validation, retest, or larger follow-up pairs that can be routed into Figure 1A strict D/N rows, Figure 1B D-equivalent binary/clinical rows, native-effect retention rows, or coverage-only/no-repull ledgers.

This is not a request for more replication corpora. It is a recall-auditable search over bibliographic metadata, open full text, repositories, citation-forward links, and domain-specific paper lanes.

The candidate grain is `original_work x replication_work x original_study/result x replication_study/result x outcome x contrast/timepoint x aggregation_level`. Do not collapse a multi-study paper pair into one row unless the source itself reports a pooled estimate at that same aggregation level.

## Required Search Surfaces

Use as many of these as available in your environment:

- OpenAlex, Crossref, Semantic Scholar, PubMed, EuropePMC, and Google Scholar-style metadata search.
- PMC, PLOS, EuropePMC, and open publisher full-text search.
- OSF, Figshare, Dataverse, Zenodo, GitHub, Dryad, ICPSR, and institutional repositories.
- ClinicalTrials.gov/PubMed trial pages for larger clinical follow-ups.
- Citation-forward search from known original papers and citation-backward search from candidate replication papers.

## Query Campaign

Use the design contract in `steps/searches/figure1/individualrepsearch-design.yml` and the query families in `steps/searches/figure1/individualrepsearch-vast-query-bank.tsv`. Start with priority 1 and 2 rows. Before long-tail mining, check the recall probes in `steps/searches/figure1/individualrepsearch-known-good-recall-probes.tsv`.

If a query family fails to recover obvious probes such as power posing, Bem/Ritchie, goal priming, physical warmth, or analytic-thinking/religion, expand that phrase family before continuing.

## Candidate Rules

Accept a lead only when there is affirmative original/replication relation evidence: self-described replication, registered replication report, failed-to-replicate article, larger confirmatory trial, independent validation, or a source table/data package that explicitly maps original and replication sides.

Score relation evidence using `steps/searches/figure1/individualrepsearch-relation-evidence-scale.tsv` and `steps/searches/figure1/individualrepsearch-routing-score-rules.tsv`. Relation score must be at least 4 before value extraction. A lower score is seed-only or manual screen, not a Figure 1 candidate.

Reject or route away from Figure 1A when the hit is only a review, same-data reanalysis, computational-only reproduction, ordinary citation, one-arm ORR without comparator, or a clinical development sequence with no explicit same/close endpoint follow-up relation.

## Output

Return JSON only, using the schema in `steps/searches/figure1/individualrepsearch-candidate-schema.json`. Include:

- original and replication bibliographic identities, including DOI/PMID/PMCID/NCT/URLs where available;
- source-object URLs to mirror first;
- relationship evidence and where it was seen;
- whether original effect, original N, replication effect, and replication N are available;
- effect metric and conversion route;
- dedupe risk and likely overlap with existing source families;
- high-confidence rejections and the exact reason;
- searches run, including query text, search surface, useful hits, and notes.

Batch size target: 25-75 candidate leads per returned manifest, with high precision. Use separate manifests by surface or campaign phase when possible, for example `individualrepsearch-openalex-direct-language-batch001.json` or `individualrepsearch-osf-source-packages-batch001.json`.

## After Return

Save the JSON under `steps/searches/figure1/individualrepsearch-*.json`, then run:

```text
make figure1-individual-replication-search-intake
make figure1-individual-replication-mirror-batch001
make figure1-individual-replication-value-scan-batch001
make figure1-individual-replication-promote-ready
```
