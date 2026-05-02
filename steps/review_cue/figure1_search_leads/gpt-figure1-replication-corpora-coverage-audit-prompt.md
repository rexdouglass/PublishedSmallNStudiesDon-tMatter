# GPT Prompt: Figure 1 Replication Corpora/Datasets Coverage Audit

We are building Figure 1 for a provenance-heavy research project. Figure 1 is about larger-N replication or follow-up results paired to their original results. We do **not** require the original or replication to be published for Figure 1. We search replication-first: find replication projects/corpora/databases/packages, then resolve both the replication/follow-up and original source.

Our constraints:

- We are doing this free-ish with local Codex, public APIs, public repository metadata, and rare manual hand-copying into GPT.
- We cannot rely on paid databases or broad proprietary indexes.
- We use target files as DAG outputs. If a search output exists, the step skips unless we pass a replace flag.
- We do not throw away leads. We classify them as corpus/database candidates, repository packages, individual replication papers, context/methods papers, duplicates, or rejects.
- We only want source-family/corpus/database discovery here. Individual replication papers are relevant later but should not be mixed into the corpus/database table unless they expose a reusable multi-row source object.

Current infrastructure:

- Root strategy file: `PROVENANCE_PIPELINE_SINGLE_SOURCE_OF_TRUTH.yml`
- Root intake table: `CORPORA_AND_DATABASES.tsv`
- Search outputs: `steps/searches/figure1/corporasearch-*.json`
- Yield summary: `steps/searches/figure1/searchyield-figure1-corpusdb-summary.md`
- Alias clusters: `steps/searches/figure1/alias-clusters-leads-artifacts-root-v001.json`
- Cluster review queue: `steps/review_cue/figure1_search_leads/clustered-priority-queue.tsv`

Current rough counts:

- 1 reviewed/confirmed new Figure 1 corpus/database lead so far.
- 67 deterministic expanded-search candidate leads not yet fully reviewed.
- 62 clusters currently look inventory-worthy.
- Many raw hits are individual papers, context papers, software/database false positives, or duplicates.

Current search families already represented:

- Local inventory and local file/header search.
- OSF, Dataverse, DataCite.
- OpenAlex, Crossref, Europe PMC.
- ClinicalTrials.gov for pilot/full-scale or follow-up ideas.
- Wayback for known dead repository URLs.
- Expanded repository/bibliographic/citation/domain query batches.
- Newly added provider adapters for Zenodo, Figshare, and Dryad.
- Known-source-family alias expansion around names such as FReD/FORRT Replication Database, RPP, RP:CB, Many Labs, RRR, SSRP, EERP, SCORE, LOOPR, ManyBabies, ManyPrimates, ManyClasses, Metaketa, BITSS, EGAP.

Our classification rule:

A lead should become a corpus/database candidate only if there is evidence of a reusable source object: dataset, database, registry, code/data repository, workbook, table, file inventory, source-family page, or other multi-row artifact. Mere use of replication words is not enough.

What I need from you:

1. Audit likely coverage gaps. What replication corpora, databases, multi-lab datasets, source-family projects, field-specific replication archives, or claim-replication datasets are likely missing from the search plan?
2. Suggest additional free/public search surfaces or APIs. Prioritize things that expose metadata, files, citation links, or repository records.
3. Suggest query families that are not just generic `"replication dataset"` wording. Include aliases like reproduction, reanalysis, validation, robustness, many-lab, multi-site, follow-up, benchmark, claim verification, etc.
4. Identify named source families we should explicitly seed.
5. Separate corpus/database candidates from individual paper routes. If something is likely only one replication paper, say so.
6. Suggest deterministic gates that would reduce false positives while keeping the long tail.
7. Identify any source families that are likely high value but require manual web investigation or author/library help.

Return JSON only, with this shape:

```json
{
  "coverage_assessment": {
    "confidence_we_found_major_psychology_sources": "low|medium|high",
    "confidence_we_found_cross_field_long_tail": "low|medium|high",
    "main_blind_spots": ["..."]
  },
  "missing_or_undersearched_source_families": [
    {
      "name": "...",
      "aliases": ["..."],
      "domain": "...",
      "why_figure1_relevant": "...",
      "likely_source_object_type": "database|dataset|repository|project|registry|paper_with_supplement|unknown",
      "likely_pair_evidence": "none|weak|medium|strong|unknown",
      "likely_effect_n_evidence": "none|weak|medium|strong|unknown",
      "suggested_search_queries": ["..."],
      "suggested_surfaces": ["OSF", "Dataverse", "Zenodo", "Figshare", "Dryad", "OpenAlex", "Crossref", "Semantic Scholar", "OpenAIRE", "web search", "other"],
      "triage_route": "candidate_corpus_database|candidate_repository_package|individual_paper_worklist|context_only|manual_investigation",
      "priority": "high|medium|low"
    }
  ],
  "new_search_surfaces": [
    {
      "surface": "...",
      "free_or_public": "yes|partly|unknown",
      "api_or_manual": "api|manual|both|unknown",
      "why_useful": "...",
      "first_queries_or_inputs": ["..."],
      "cautions": ["..."],
      "priority": "high|medium|low"
    }
  ],
  "new_query_families": [
    {
      "family_name": "...",
      "queries": ["..."],
      "expected_yield": "high|medium|low",
      "expected_noise": "high|medium|low",
      "recommended_gate": "..."
    }
  ],
  "deterministic_triage_rules_to_add": [
    {
      "rule_name": "...",
      "promote_if": ["..."],
      "reject_or_route_if": ["..."],
      "why": "..."
    }
  ],
  "manual_followup_targets": [
    {
      "target": "...",
      "reason": "...",
      "what_to_check": ["..."],
      "priority": "high|medium|low"
    }
  ]
}
```

Be conservative about what counts as a corpus/database. We would rather route individual papers away from `CORPORA_AND_DATABASES.tsv` than pollute the source-family table.
