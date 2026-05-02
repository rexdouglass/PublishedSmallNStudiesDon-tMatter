# GPT Field-Coding Prompt: figure1_search_leads

You are coding rows for `CORPORA_AND_DATABASES.tsv` in a provenance pipeline.
Use web research only to support the requested fields. Do not invent file contents, row counts, column names, or parser status.
If a field requires artifact/file inspection rather than surface metadata, set it to `unknown` and say what must be inspected next.

Return JSON only. The user will save it as `steps/review_cue/figure1_search_leads/apply_to_CORPORA_AND_DATABASES/gpt-field-coding-response-batch001.json`.

JSON shape:

```json
{
  "field_coding_decisions": [
    {
      "coding_task_id": "...",
      "lead_key": "...",
      "field_values": {
        "source_family": "...",
        "domain_or_field": "...",
        "description": "...",
        "why_relevant": "...",
        "result_fields_available": "...",
        "has_d_or_convertible_effect": "...",
        "has_n": "...",
        "has_replication_pair_mapping": "...",
        "has_publication_links": "...",
        "parser_family": "...",
        "blocker_codes": "...",
        "next_action": "...",
        "notes": "..."
      },
      "field_basis": {
        "source_family": "short evidence basis or unknown rationale",
        "domain_or_field": "short evidence basis or unknown rationale",
        "description": "short evidence basis or unknown rationale",
        "why_relevant": "short evidence basis or unknown rationale",
        "result_fields_available": "short evidence basis or unknown rationale",
        "has_d_or_convertible_effect": "short evidence basis or unknown rationale",
        "has_n": "short evidence basis or unknown rationale",
        "has_replication_pair_mapping": "short evidence basis or unknown rationale",
        "has_publication_links": "short evidence basis or unknown rationale",
        "parser_family": "short evidence basis or unknown rationale",
        "blocker_codes": "short evidence basis or unknown rationale",
        "next_action": "short evidence basis or unknown rationale",
        "notes": "short evidence basis or unknown rationale"
      },
      "field_confidence": {
        "source_family": "high|medium|low",
        "domain_or_field": "high|medium|low",
        "description": "high|medium|low",
        "why_relevant": "high|medium|low",
        "result_fields_available": "high|medium|low",
        "has_d_or_convertible_effect": "high|medium|low",
        "has_n": "high|medium|low",
        "has_replication_pair_mapping": "high|medium|low",
        "has_publication_links": "high|medium|low",
        "parser_family": "high|medium|low",
        "blocker_codes": "high|medium|low",
        "next_action": "high|medium|low",
        "notes": "high|medium|low"
      },
      "sources_checked": [
        "URL or file path"
      ]
    }
  ]
}
```

Allowed yes/no fields must use `yes`, `no`, or `unknown`: `has_d_or_convertible_effect`, `has_n`, `has_replication_pair_mapping`, `has_publication_links`.

Rows to code:

## 1. A large-scale replication of scenario-based experiments in psychology and management using large language models
- coding_task_id: `fieldcode_title_a_large_scale_replication_of_scenario_based_experiments_in_psychology_and_management_using_large_language_models`
- lead_key: `title:a_large_scale_replication_of_scenario_based_experiments_in_psychology_and_management_using_large_language_models`
- landing_url: `https://doi.org/10.1038/s43588-025-00840-7`
- source_key: `10.1038/s43588-025-00840-7 | doi:10.1038/s43588-025-00840-7`
- fields_to_code: `domain_or_field | description | why_relevant | has_d_or_convertible_effect | has_n | has_replication_pair_mapping | parser_family`

Evidence packet:

```json
{
  "current_description": "",
  "current_notes": "provider=crossref | external_id=10.1038/s43588-025-00840-7 | doi=10.1038/s43588-025-00840-7 | review_cue=figure1_search_leads | decision=keep_in_corpora_and_databases | confidence=medium | reason=The Nature Computational Science article title identifies a large-scale replication of scenario-based experiments. It is plausibly a multi-study source-family candidate, but source inventory must confirm whether article data or supplements expose original/replication mapping and usable result fields.",
  "current_why_relevant": "Matched Figure 1 bibliographic search query '\"large-scale replication\" \"dataset\"'; lead_classification=corpus_database_or_project_signal; score=9; reasons=strong_phrase:large-scale replication | replication_word | metadata_corpus_signal",
  "decision": "keep_in_corpora_and_databases",
  "landing_url": "https://doi.org/10.1038/s43588-025-00840-7",
  "lead_key": "title:a_large_scale_replication_of_scenario_based_experiments_in_psychology_and_management_using_large_language_models",
  "name": "A large-scale replication of scenario-based experiments in psychology and management using large language models",
  "proposal_basis": "The Nature Computational Science article title identifies a large-scale replication of scenario-based experiments. It is plausibly a multi-study source-family candidate, but source inventory must confirm whether article data or supplements expose original/replication mapping and usable result fields.",
  "source_key": "10.1038/s43588-025-00840-7 | doi:10.1038/s43588-025-00840-7"
}
```

## 2. A multi-site Registered Replication Report of Olson &amp; Fazio (2001) "Implicit Attitude Formation Through Classical Conditioning"
- coding_task_id: `fieldcode_title_a_multi_site_registered_replication_report_of_olson_amp_fazio_2001_implicit_attitude_formation_through_classical_conditi`
- lead_key: `title:a_multi_site_registered_replication_report_of_olson_amp_fazio_2001_implicit_attitude_formation_through_classical_conditi`
- landing_url: `https://osf.io/3hjpf/`
- source_key: `3hjpf`
- fields_to_code: `domain_or_field | why_relevant | has_d_or_convertible_effect | has_n | has_replication_pair_mapping | has_publication_links | parser_family`

Evidence packet:

```json
{
  "current_description": "NB nomenclature has changed over time: despite title of original article, \"implicit\" here refers to self-reported attitudes that were acquired in the absence of awareness/memory of the CS-US pairings (rather than classical conditioning procedures giving rise to implicit attitudes)",
  "current_notes": "provider=osf | external_id=3hjpf | doi= | review_cue=figure1_search_leads | decision=keep_in_corpora_and_databases | confidence=high | reason=The stale OSF 3hjpf lead is the Olson and Fazio registered replication source family | the canonical public project is OSF hs32y and the article DOI is 10.1177/0956797620968526. It should be kept but deduplicated to that canonical route.",
  "current_why_relevant": "Matched Figure 1 repository search query '\"registered replication report\" data'; lead_classification=corpus_database_or_project_signal; score=9; reasons=strong_phrase:registered replication report | replication_word | original_word",
  "decision": "keep_in_corpora_and_databases",
  "landing_url": "https://osf.io/3hjpf/",
  "lead_key": "title:a_multi_site_registered_replication_report_of_olson_amp_fazio_2001_implicit_attitude_formation_through_classical_conditi",
  "name": "A multi-site Registered Replication Report of Olson &amp; Fazio (2001) \"Implicit Attitude Formation Through Classical Conditioning\"",
  "proposal_basis": "The stale OSF 3hjpf lead is the Olson and Fazio registered replication source family; the canonical public project is OSF hs32y and the article DOI is 10.1177/0956797620968526. It should be kept but deduplicated to that canonical route.",
  "source_key": "3hjpf"
}
```

## 3. A Multilab Preregistered Replication of the Ego-Depletion Effect
- coding_task_id: `fieldcode_title_a_multilab_preregistered_replication_of_the_ego_depletion_effect`
- lead_key: `title:a_multilab_preregistered_replication_of_the_ego_depletion_effect`
- landing_url: `https://doi.org/10.1177/1745691616652873`
- source_key: `https://openalex.org/W2499154041 | doi:10.1177/1745691616652873`
- fields_to_code: `domain_or_field | why_relevant | has_d_or_convertible_effect | has_replication_pair_mapping | parser_family`

Evidence packet:

```json
{
  "current_description": "Good self-control has been linked to adaptive outcomes such as better health, cohesive personal relationships, success in the workplace and at school, and less susceptibility to crime and addictions. In contrast, self-control failure is linked to maladaptive outcomes. Understanding the mechanisms by which self-control predicts behavior may assist in promoting better regulation and outcomes. A popular approach to understanding self-control is the strength or resource depletion model. Self-control is conceptualized as a limited resource that becomes depleted after a period of exertion resulting in self-control failure. The model has typically been tested using a sequential-task experimental paradigm, in which people completing an initial self-control task have reduced self-control capacity and poorer performance on a subsequent task, a state known as ego depletion Although a meta-analysis of ego-depletion experiments found a medium-sized effect, subsequent meta-analyses have questioned the size and existence of the effect and identified instances of possible bias. The analyses served as a catalyst for the current Registered Replication Report of the ego-depletion effect. Multiple laboratories (k = 23, total N = 2,141) conducted replications of a standardized ego-depletion protocol based on a sequential-task paradigm by Sripada et al. Meta-analysis of the studies revealed that the size of the ego-depletion effect was small with 95% confidence intervals (CIs) that encompassed zero (d = 0.04, 95% CI [-0.07, 0.15]. We discuss implications of the findings for the ego-depletion eff",
  "current_notes": "provider=openalex | external_id=https://openalex.org/W2499154041 | doi=https://doi.org/10.1177/1745691616652873 | review_cue=figure1_search_leads | decision=keep_in_corpora_and_databases | confidence=high | reason=This Registered Replication Report is a multi-lab source-family candidate: the abstract reports 23 laboratories and N=2141 for a standardized ego-depletion replication protocol. It should stay for source inventory and table extraction review.",
  "current_why_relevant": "Matched Figure 1 citation search query '\"registered replication report\" \"many labs\"'; lead_classification=corpus_database_or_project_signal; score=7; reasons=strong_phrase:registered replication report | replication_word",
  "decision": "keep_in_corpora_and_databases",
  "landing_url": "https://doi.org/10.1177/1745691616652873",
  "lead_key": "title:a_multilab_preregistered_replication_of_the_ego_depletion_effect",
  "name": "A Multilab Preregistered Replication of the Ego-Depletion Effect",
  "proposal_basis": "This Registered Replication Report is a multi-lab source-family candidate: the abstract reports 23 laboratories and N=2141 for a standardized ego-depletion replication protocol. It should stay for source inventory and table extraction review.",
  "source_key": "https://openalex.org/W2499154041 | doi:10.1177/1745691616652873"
}
```

## 4. An open investigation of the reproducibility of cancer biology research
- coding_task_id: `fieldcode_title_an_open_investigation_of_the_reproducibility_of_cancer_biology_research`
- lead_key: `title:an_open_investigation_of_the_reproducibility_of_cancer_biology_research`
- landing_url: `https://doi.org/10.7554/elife.04333`
- source_key: `https://openalex.org/W2142148275 | rpcb | doi:10.7554/elife.04333`
- fields_to_code: `domain_or_field | why_relevant | has_d_or_convertible_effect | has_n | has_replication_pair_mapping | parser_family`

Evidence packet:

```json
{
  "current_description": "It is widely believed that research that builds upon previously published findings has reproduced the original work. However, it is rare for researchers to perform or publish direct replications of existing results. The Reproducibility Project: Cancer Biology is an open investigation of reproducibility in preclinical cancer biology research. We have identified 50 high impact cancer biology articles published in the period 2010-2012, and plan to replicate a subset of experimental results from each article. A Registered Report detailing the proposed experimental designs and protocols for each subset of experiments will be peer reviewed and published prior to data collection. The results of these experiments will then be published in a Replication Study. The resulting open methodology and dataset will provide evidence about the reproducibility of high-impact results, and an opportunity to identify predictors of reproducibility.",
  "current_notes": "provider=openalex | external_id=https://openalex.org/W2142148275 | doi=https://doi.org/10.7554/elife.04333 | review_cue=figure1_search_leads | decision=keep_in_corpora_and_databases | confidence=high | reason=This eLife article defines the Reproducibility Project: Cancer Biology source family, identifying 50 high-impact cancer biology articles and planned replication studies. It should be retained but deduplicated with the later RPCB result-data source-family records.",
  "current_why_relevant": "Matched Figure 1 citation search query '\"Reproducibility Project: Psychology\" dataset replication'; lead_classification=corpus_database_or_project_signal; score=13; reasons=strong_phrase:reproducibility project | data_term:data | data_term:dataset | replication_word | original_word | metadata_corpus_signal",
  "decision": "keep_in_corpora_and_databases",
  "landing_url": "https://doi.org/10.7554/elife.04333",
  "lead_key": "title:an_open_investigation_of_the_reproducibility_of_cancer_biology_research",
  "name": "An open investigation of the reproducibility of cancer biology research",
  "proposal_basis": "This eLife article defines the Reproducibility Project: Cancer Biology source family, identifying 50 high-impact cancer biology articles and planned replication studies. It should be retained but deduplicated with the later RPCB result-data source-family records.",
  "source_key": "https://openalex.org/W2142148275 | rpcb | doi:10.7554/elife.04333"
}
```

## 5. Reproducibility Project - Psychology: Design
- coding_task_id: `fieldcode_title_reproducibility_project_psychology_design`
- lead_key: `title:reproducibility_project_psychology_design`
- landing_url: `https://osf.io/i68pe/`
- source_key: `i68pe | osf:i68pe`
- fields_to_code: `domain_or_field | description | why_relevant | has_d_or_convertible_effect | has_n | has_replication_pair_mapping | has_publication_links | parser_family`

Evidence packet:

```json
{
  "current_description": "",
  "current_notes": "provider=osf | external_id=i68pe | doi= | review_cue=figure1_search_leads | decision=keep_in_corpora_and_databases | confidence=high | reason=This is a real Reproducibility Project: Psychology OSF project/source-family lead. It belongs in the root corpus/database inventory because it can expose multiple original/replication pair rows after file-level inventory.",
  "current_why_relevant": "Matched Figure 1 repository search query '\"Reproducibility Project\" coded data'; lead_classification=corpus_database_or_project_signal; score=5; reasons=strong_phrase:reproducibility project",
  "decision": "keep_in_corpora_and_databases",
  "landing_url": "https://osf.io/i68pe/",
  "lead_key": "title:reproducibility_project_psychology_design",
  "name": "Reproducibility Project - Psychology: Design",
  "proposal_basis": "This is a real Reproducibility Project: Psychology OSF project/source-family lead. It belongs in the root corpus/database inventory because it can expose multiple original/replication pair rows after file-level inventory.",
  "source_key": "i68pe | osf:i68pe"
}
```

## 6. Rescience C Contents
- coding_task_id: `fieldcode_title_rescience_c_contents`
- lead_key: `title:rescience_c_contents`
- landing_url: ``
- source_key: `https://rescience.github.io/read/`
- fields_to_code: `source_family | domain_or_field | description | result_fields_available | has_d_or_convertible_effect | has_n | has_replication_pair_mapping | has_publication_links | parser_family`

Evidence packet:

```json
{
  "current_description": "",
  "current_notes": "review_cue=figure1_search_leads | decision=promote_to_corpora_and_databases | confidence=high | reason=ReScience C is a journal/source-family contents page for computational replication articles, with many article records and code/review metadata. It is a reusable source-family object rather than a single paper.",
  "current_why_relevant": "ReScience C is a journal/source-family contents page for computational replication articles, with many article records and code/review metadata. It is a reusable source-family object rather than a single paper.",
  "decision": "promote_to_corpora_and_databases",
  "landing_url": "",
  "lead_key": "title:rescience_c_contents",
  "name": "Rescience C Contents",
  "proposal_basis": "ReScience C is a journal/source-family contents page for computational replication articles, with many article records and code/review metadata. It is a reusable source-family object rather than a single paper.",
  "source_key": "https://rescience.github.io/read/"
}
```
