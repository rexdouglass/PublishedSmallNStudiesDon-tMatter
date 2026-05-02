# Clustered Codex Review: Figure 1 Search Leads

Review source-family clusters, not isolated search hits. Use the aliases/artifacts in each cluster to decide what the cluster is.

Do not edit root tables. Save JSON decisions using the contract below.

Save decisions as: `steps/review_cue/figure1_search_leads/reviewcue-clustered-decisions-figure1_search_leads-codex-clustered005.json`

Allowed cluster decisions:
- keep_source_family_candidate
- inventory_source_family_artifacts
- route_cluster_to_result_table_worklist
- route_cluster_to_individual_replication_paper_worklist
- keep_cluster_as_context
- reject_cluster_irrelevant
- needs_more_evidence

Decision rule:
- Keep/inventory a cluster only when there is evidence of a reusable source object: dataset, database, registry, code/data repository, workbook, table, file inventory, or explicit source-family page.
- Route individual replication papers away from corpus/database intake unless they expose a reusable multi-row source.
- Do not infer file contents from titles alone.
- If a cluster contains child artifacts under a source family, say which parent source-family row should own them.

Return JSON only:

```json
{
  "cluster_decisions": [
    {
      "cluster_id": "...",
      "decision": "keep_source_family_candidate|inventory_source_family_artifacts|route_cluster_to_result_table_worklist|route_cluster_to_individual_replication_paper_worklist|keep_cluster_as_context|reject_cluster_irrelevant|needs_more_evidence",
      "confidence": "high|medium|low",
      "preferred_source_family_name": "...",
      "parent_corpus_database_id_or_key": "...",
      "reason": "...",
      "next_action": "...",
      "sources_checked": [
        "..."
      ],
      "lead_level_notes": [
        {
          "node_id": "...",
          "suggested_disposition": "root_source_family|child_artifact|individual_paper|context|reject|needs_more_evidence",
          "notes": "..."
        }
      ]
    }
  ]
}
```

Clusters:

## 1. dataverse manifest
- cluster_id: `cluster_dataverse_manifest_ee14f1be8828`
- priority: `high / 104`
- confidence: `strict`
- preferred_family_hint: `many_labs`
- node_count: `23`; open_review_count: `23`; omitted_node_count: `11`
- strict_keys: `lead_harvest:covid_online_2021`
- record_kind_counts: `{"candidate_individual_paper_or_package": 3, "candidate_result_table": 20}`
- inventory_status_counts: `{"needs_triage_search_lead": 20, "routed_to_individual_paper_search": 3}`

Compact nodes:

```json
[
  {
    "inventory_status": "routed_to_individual_paper_search",
    "landing_url": "data/raw/replication_projects/lead_harvest/covid_online_2021/unpacked_work/ReadMe.R",
    "manifest_path": "steps/searches/figure1/corporasearch-code-expanded-local-pair-field-signatures.json",
    "name": "ReadMe",
    "next_action": "route_to_individual_replication_paper_worklist",
    "node_id": "node_search_manifest_eef116d0abcd",
    "node_source": "search_manifest",
    "record_kind": "candidate_individual_paper_or_package",
    "review_queue_status": "needs_review",
    "source_key": "data/raw/replication_projects/lead_harvest/covid_online_2021/unpacked_work/ReadMe.R",
    "why_relevant": "Matched Figure 1 code search query 'study_pair_id original replication'; lead_classification=individual_paper_or_one_off_package_signal; score=10; reasons=data_term:data | data_term:code | replication_word | original_word | local_table_or_code_surface | query_phrase_in_text"
  },
  {
    "inventory_status": "needs_triage_search_lead",
    "landing_url": "data/raw/replication_projects/lead_harvest/covid_online_2021/unpacked_work/appendix_section_a.R",
    "manifest_path": "steps/searches/figure1/corporasearch-code-expanded-local-pair-field-signatures.json",
    "name": "appendix section a",
    "next_action": "triage_file_for_pair_table_or_source_family",
    "node_id": "node_search_manifest_b3912b8bbcd5",
    "node_source": "search_manifest",
    "record_kind": "candidate_result_table",
    "review_queue_status": "needs_review",
    "source_key": "data/raw/replication_projects/lead_harvest/covid_online_2021/unpacked_work/appendix_section_a.R",
    "why_relevant": "Matched Figure 1 code search query 'study_pair_id original replication'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=8; reasons=data_term:data | data_term:code | data_term:osf | replication_word | original_word | query_phrase_in_text"
  },
  {
    "inventory_status": "needs_triage_search_lead",
    "landing_url": "data/raw/replication_projects/lead_harvest/covid_online_2021/unpacked_work/conjoint_original.dta",
    "manifest_path": "steps/searches/figure1/corporasearch-code-expanded-local-pair-field-signatures.json",
    "name": "conjoint original",
    "next_action": "triage_file_for_pair_table_or_source_family",
    "node_id": "node_search_manifest_966c422388ab",
    "node_source": "search_manifest",
    "record_kind": "candidate_result_table",
    "review_queue_status": "needs_review",
    "source_key": "data/raw/replication_projects/lead_harvest/covid_online_2021/unpacked_work/conjoint_original.dta",
    "why_relevant": "Matched Figure 1 code search query 'study_pair_id original replication'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=9; reasons=data_term:data | replication_word | original_word | local_table_or_code_surface | query_phrase_in_text"
  },
  {
    "inventory_status": "needs_triage_search_lead",
    "landing_url": "data/raw/replication_projects/lead_harvest/covid_online_2021/dataverse_03_download.json",
    "manifest_path": "steps/searches/figure1/corporasearch-code-expanded-local-pair-field-signatures.json",
    "name": "dataverse 03 download",
    "next_action": "triage_file_for_pair_table_or_source_family",
    "node_id": "node_search_manifest_39bc0b83828e",
    "node_source": "search_manifest",
    "record_kind": "candidate_result_table",
    "review_queue_status": "needs_review",
    "source_key": "data/raw/replication_projects/lead_harvest/covid_online_2021/dataverse_03_download.json",
    "why_relevant": "Matched Figure 1 code search query 'study_pair_id original replication'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=11; reasons=data_term:data | data_term:code | data_term:dataverse | replication_word | original_word | local_table_or_code_surface | query_phrase_in_text"
  },
  {
    "inventory_status": "needs_triage_search_lead",
    "landing_url": "data/raw/replication_projects/lead_harvest/covid_online_2021/dataverse_04_download.json",
    "manifest_path": "steps/searches/figure1/corporasearch-code-expanded-local-pair-field-signatures.json",
    "name": "dataverse 04 download",
    "next_action": "triage_file_for_pair_table_or_source_family",
    "node_id": "node_search_manifest_eaba2b0dcd60",
    "node_source": "search_manifest",
    "record_kind": "candidate_result_table",
    "review_queue_status": "needs_review",
    "source_key": "data/raw/replication_projects/lead_harvest/covid_online_2021/dataverse_04_download.json",
    "why_relevant": "Matched Figure 1 code search query 'study_pair_id original replication'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=11; reasons=data_term:data | data_term:code | data_term:dataverse | replication_word | original_word | local_table_or_code_surface | query_phrase_in_text"
  },
  {
    "inventory_status": "needs_triage_search_lead",
    "landing_url": "data/raw/replication_projects/lead_harvest/covid_online_2021/dataverse_04__gilens_original.rds",
    "manifest_path": "steps/searches/figure1/corporasearch-code-expanded-local-pair-field-signatures.json",
    "name": "dataverse 04 gilens original",
    "next_action": "triage_file_for_pair_table_or_source_family",
    "node_id": "node_search_manifest_e6c8b3be4253",
    "node_source": "search_manifest",
    "record_kind": "candidate_result_table",
    "review_queue_status": "needs_review",
    "source_key": "data/raw/replication_projects/lead_harvest/covid_online_2021/dataverse_04__gilens_original.rds",
    "why_relevant": "Matched Figure 1 code search query 'study_pair_id original replication'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=10; reasons=data_term:data | data_term:dataverse | replication_word | original_word | local_table_or_code_surface | query_phrase_in_text"
  },
  {
    "inventory_status": "needs_triage_search_lead",
    "landing_url": "data/raw/replication_projects/lead_harvest/covid_online_2021/dataverse_06_download.json",
    "manifest_path": "steps/searches/figure1/corporasearch-code-expanded-local-pair-field-signatures.json",
    "name": "dataverse 06 download",
    "next_action": "triage_file_for_pair_table_or_source_family",
    "node_id": "node_search_manifest_9e9cd74f6ea9",
    "node_source": "search_manifest",
    "record_kind": "candidate_result_table",
    "review_queue_status": "needs_review",
    "source_key": "data/raw/replication_projects/lead_harvest/covid_online_2021/dataverse_06_download.json",
    "why_relevant": "Matched Figure 1 code search query 'study_pair_id original replication'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=11; reasons=data_term:data | data_term:code | data_term:dataverse | replication_word | original_word | local_table_or_code_surface | query_phrase_in_text"
  },
  {
    "inventory_status": "needs_triage_search_lead",
    "landing_url": "data/raw/replication_projects/lead_harvest/covid_online_2021/dataverse_06__psv_original.rds",
    "manifest_path": "steps/searches/figure1/corporasearch-code-expanded-local-pair-field-signatures.json",
    "name": "dataverse 06 psv original",
    "next_action": "triage_file_for_pair_table_or_source_family",
    "node_id": "node_search_manifest_9d4908a346a6",
    "node_source": "search_manifest",
    "record_kind": "candidate_result_table",
    "review_queue_status": "needs_review",
    "source_key": "data/raw/replication_projects/lead_harvest/covid_online_2021/dataverse_06__psv_original.rds",
    "why_relevant": "Matched Figure 1 code search query 'study_pair_id original replication'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=10; reasons=data_term:data | data_term:dataverse | replication_word | original_word | local_table_or_code_surface | query_phrase_in_text"
  },
  {
    "inventory_status": "needs_triage_search_lead",
    "landing_url": "data/raw/replication_projects/lead_harvest/covid_online_2021/dataverse_07_download.json",
    "manifest_path": "steps/searches/figure1/corporasearch-code-expanded-local-pair-field-signatures.json",
    "name": "dataverse 07 download",
    "next_action": "triage_file_for_pair_table_or_source_family",
    "node_id": "node_search_manifest_486db6ebe344",
    "node_source": "search_manifest",
    "record_kind": "candidate_result_table",
    "review_queue_status": "needs_review",
    "source_key": "data/raw/replication_projects/lead_harvest/covid_online_2021/dataverse_07_download.json",
    "why_relevant": "Matched Figure 1 code search query 'study_pair_id original replication'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=11; reasons=data_term:data | data_term:code | data_term:dataverse | replication_word | original_word | local_table_or_code_surface | query_phrase_in_text"
  },
  {
    "inventory_status": "needs_triage_search_lead",
    "landing_url": "data/raw/replication_projects/lead_harvest/covid_online_2021/dataverse_07__tw_original.rds",
    "manifest_path": "steps/searches/figure1/corporasearch-code-expanded-local-pair-field-signatures.json",
    "name": "dataverse 07 tw original",
    "next_action": "triage_file_for_pair_table_or_source_family",
    "node_id": "node_search_manifest_e055474e7a92",
    "node_source": "search_manifest",
    "record_kind": "candidate_result_table",
    "review_queue_status": "needs_review",
    "source_key": "data/raw/replication_projects/lead_harvest/covid_online_2021/dataverse_07__tw_original.rds",
    "why_relevant": "Matched Figure 1 code search query 'study_pair_id original replication'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=10; reasons=data_term:data | data_term:dataverse | replication_word | original_word | local_table_or_code_surface | query_phrase_in_text"
  },
  {
    "inventory_status": "needs_triage_search_lead",
    "landing_url": "data/raw/replication_projects/lead_harvest/covid_online_2021/dataverse_09_download.json",
    "manifest_path": "steps/searches/figure1/corporasearch-code-expanded-local-pair-field-signatures.json",
    "name": "dataverse 09 download",
    "next_action": "triage_file_for_pair_table_or_source_family",
    "node_id": "node_search_manifest_86982301af30",
    "node_source": "search_manifest",
    "record_kind": "candidate_result_table",
    "review_queue_status": "needs_review",
    "source_key": "data/raw/replication_projects/lead_harvest/covid_online_2021/dataverse_09_download.json",
    "why_relevant": "Matched Figure 1 code search query 'study_pair_id original replication'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=11; reasons=data_term:data | data_term:code | data_term:dataverse | replication_word | original_word | local_table_or_code_surface | query_phrase_in_text"
  },
  {
    "inventory_status": "needs_triage_search_lead",
    "landing_url": "data/raw/replication_projects/lead_harvest/covid_online_2021/dataverse_09__pwk_original.rds",
    "manifest_path": "steps/searches/figure1/corporasearch-code-expanded-local-pair-field-signatures.json",
    "name": "dataverse 09 pwk original",
    "next_action": "triage_file_for_pair_table_or_source_family",
    "node_id": "node_search_manifest_4c019452646e",
    "node_source": "search_manifest",
    "record_kind": "candidate_result_table",
    "review_queue_status": "needs_review",
    "source_key": "data/raw/replication_projects/lead_harvest/covid_online_2021/dataverse_09__pwk_original.rds",
    "why_relevant": "Matched Figure 1 code search query 'study_pair_id original replication'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=10; reasons=data_term:data | data_term:dataverse | replication_word | original_word | local_table_or_code_surface | query_phrase_in_text"
  }
]
```

## 2. osf 01 Original Dataset
- cluster_id: `cluster_osf_01_original_dataset_63864d88187b`
- priority: `high / 104`
- confidence: `strict`
- preferred_family_hint: ``
- node_count: `6`; open_review_count: `5`; omitted_node_count: `0`
- strict_keys: `lead_harvest:contextual_bias_2026`
- record_kind_counts: `{"candidate_result_table": 6}`
- inventory_status_counts: `{"needs_triage_search_lead": 6}`

Compact nodes:

```json
[
  {
    "inventory_status": "needs_triage_search_lead",
    "landing_url": "data/raw/replication_projects/lead_harvest/contextual_bias_2026/osf_01__Original_Dataset.sav",
    "manifest_path": "steps/searches/figure1/corporasearch-code-expanded-local-pair-field-signatures.json",
    "name": "osf 01 Original Dataset",
    "next_action": "triage_file_for_pair_table_or_source_family",
    "node_id": "node_search_manifest_281ebaea6cc9",
    "node_source": "search_manifest",
    "record_kind": "candidate_result_table",
    "review_queue_status": "needs_review",
    "source_key": "data/raw/replication_projects/lead_harvest/contextual_bias_2026/osf_01__Original_Dataset.sav",
    "why_relevant": "Matched Figure 1 code search query 'study_pair_id original replication'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=11; reasons=data_term:data | data_term:dataset | data_term:osf | replication_word | original_word | local_table_or_code_surface | query_phrase_in_text"
  },
  {
    "inventory_status": "needs_triage_search_lead",
    "landing_url": "data/raw/replication_projects/lead_harvest/contextual_bias_2026/osf_01_download.json",
    "manifest_path": "steps/searches/figure1/corporasearch-code-expanded-local-pair-field-signatures.json",
    "name": "osf 01 download",
    "next_action": "triage_file_for_pair_table_or_source_family",
    "node_id": "node_search_manifest_fec7dd408b30",
    "node_source": "search_manifest",
    "record_kind": "candidate_result_table",
    "review_queue_status": "needs_review",
    "source_key": "data/raw/replication_projects/lead_harvest/contextual_bias_2026/osf_01_download.json",
    "why_relevant": "Matched Figure 1 code search query 'study_pair_id original replication'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=12; reasons=data_term:data | data_term:dataset | data_term:code | data_term:osf | replication_word | original_word | local_table_or_code_surface | query_phrase_in_text"
  },
  {
    "inventory_status": "needs_triage_search_lead",
    "landing_url": "data/raw/replication_projects/lead_harvest/contextual_bias_2026/osf_04__FinalData.R",
    "manifest_path": "steps/searches/figure1/corporasearch-code-expanded-local-pair-field-signatures.json",
    "name": "osf 04 FinalData",
    "next_action": "triage_file_for_pair_table_or_source_family",
    "node_id": "node_search_manifest_d7f6cde01cf8",
    "node_source": "search_manifest",
    "record_kind": "candidate_result_table",
    "review_queue_status": "needs_review",
    "source_key": "data/raw/replication_projects/lead_harvest/contextual_bias_2026/osf_04__FinalData.R",
    "why_relevant": "Matched Figure 1 code search query 'study_pair_id original replication'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=8; reasons=data_term:data | data_term:code | data_term:osf | replication_word | original_word | query_phrase_in_text"
  },
  {
    "inventory_status": "needs_triage_search_lead",
    "landing_url": "data/raw/replication_projects/lead_harvest/contextual_bias_2026/osf_05__FinalData.R",
    "manifest_path": "steps/searches/figure1/corporasearch-code-expanded-local-pair-field-signatures.json",
    "name": "osf 05 FinalData",
    "next_action": "triage_file_for_pair_table_or_source_family",
    "node_id": "node_search_manifest_0831ed595724",
    "node_source": "search_manifest",
    "record_kind": "candidate_result_table",
    "review_queue_status": "needs_review",
    "source_key": "data/raw/replication_projects/lead_harvest/contextual_bias_2026/osf_05__FinalData.R",
    "why_relevant": "Matched Figure 1 code search query 'study_pair_id original replication'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=8; reasons=data_term:data | data_term:code | data_term:osf | replication_word | original_word | query_phrase_in_text"
  },
  {
    "inventory_status": "needs_triage_search_lead",
    "landing_url": "data/raw/replication_projects/lead_harvest/contextual_bias_2026/osf_manifest.json",
    "manifest_path": "steps/searches/figure1/corporasearch-code-expanded-local-pair-field-signatures.json",
    "name": "osf manifest",
    "next_action": "triage_file_for_pair_table_or_source_family",
    "node_id": "node_search_manifest_c81af09ab4ca",
    "node_source": "search_manifest",
    "record_kind": "candidate_result_table",
    "review_queue_status": "needs_review",
    "source_key": "data/raw/replication_projects/lead_harvest/contextual_bias_2026/osf_manifest.json",
    "why_relevant": "Matched Figure 1 code search query 'study_pair_id original replication'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=10; reasons=data_term:data | data_term:osf | replication_word | original_word | local_table_or_code_surface | query_phrase_in_text"
  },
  {
    "inventory_status": "needs_triage_search_lead",
    "landing_url": "data/raw/replication_projects/lead_harvest/contextual_bias_2026/osf_file_list.csv",
    "manifest_path": "steps/searches/figure1/corporasearch-code-expanded-local-pair-field-signatures.json",
    "name": "osf file list",
    "next_action": "triage_file_for_pair_table_or_source_family",
    "node_id": "node_search_manifest_cdebf5a3ff73",
    "node_source": "search_manifest",
    "record_kind": "candidate_result_table",
    "review_queue_status": "",
    "source_key": "data/raw/replication_projects/lead_harvest/contextual_bias_2026/osf_file_list.csv",
    "why_relevant": "Matched Figure 1 code search query 'study_pair_id original replication'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=10; reasons=data_term:data | data_term:osf | replication_word | original_word | local_table_or_code_surface | query_phrase_in_text"
  }
]
```

## 3. Many Labs 2: Investigating Variation in Replicability Across Samples and Settings
- cluster_id: `cluster_many_labs_2_investigating_variation_in_replicability_across_samples_and_settings_9638ac62afe8`
- priority: `high / 98`
- confidence: `strict`
- preferred_family_hint: `many_labs`
- node_count: `7`; open_review_count: `7`; omitted_node_count: `0`
- strict_keys: `doi:10.1177/2515245918810225 | url:https://doi.org/10.1177/2515245918810225 | title:many_labs_2_investigating_variation_in_replicability_across_samples_and_settings`
- record_kind_counts: `{"candidate_corpus_or_database": 7}`
- inventory_status_counts: `{"discovered_search_lead": 7}`

Compact nodes:

```json
[
  {
    "inventory_status": "discovered_search_lead",
    "landing_url": "https://doi.org/10.1177/2515245918810225",
    "manifest_path": "steps/searches/figure1/corporasearch-citation-snowball-known-replication-corpora.json",
    "name": "Many Labs 2: Investigating Variation in Replicability Across Samples and Settings",
    "next_action": "triage_landing_page_or_package_for_pair_table",
    "node_id": "node_root_table_d6e9f7e1cdef",
    "node_source": "root_table",
    "record_kind": "candidate_corpus_or_database",
    "review_queue_status": "needs_root_candidate_review",
    "source_key": "https://openalex.org/W2776961836",
    "why_relevant": "Matched Figure 1 citation search query '\"Many Labs\" replication project dataset'; lead_classification=corpus_database_or_project_signal; score=17; reasons=strong_phrase:many labs | pair_term:original effect | pair_term:replication effect | pair_term:effect size | pair_term:cohen | replication_word | original_word"
  },
  {
    "inventory_status": "discovered_search_lead",
    "landing_url": "https://doi.org/10.1177/2515245918810225",
    "manifest_path": "steps/searches/figure1/corporasearch-alternate-vocab-expanded-reproduction-reanalysis-validation-followup.json",
    "name": "Many Labs 2: Investigating Variation in Replicability Across Samples and Settings",
    "next_action": "triage_landing_page_or_package_for_pair_table",
    "node_id": "node_search_manifest_de773ac17cfd",
    "node_source": "search_manifest",
    "record_kind": "candidate_corpus_or_database",
    "review_queue_status": "needs_root_candidate_review",
    "source_key": "https://openalex.org/W2776961836",
    "why_relevant": "Matched Figure 1 domain search query '\"many-lab\" dataset original'; lead_classification=corpus_database_or_project_signal; score=17; reasons=strong_phrase:many labs | pair_term:original effect | pair_term:replication effect | pair_term:effect size | pair_term:cohen | replication_word | original_word"
  },
  {
    "inventory_status": "discovered_search_lead",
    "landing_url": "https://doi.org/10.1177/2515245918810225",
    "manifest_path": "steps/searches/figure1/corporasearch-bibliographic-expanded-replication-corpus-database.json",
    "name": "Many Labs 2: Investigating Variation in Replicability Across Samples and Settings",
    "next_action": "triage_landing_page_or_package_for_pair_table",
    "node_id": "node_search_manifest_61672c3be056",
    "node_source": "search_manifest",
    "record_kind": "candidate_corpus_or_database",
    "review_queue_status": "needs_root_candidate_review",
    "source_key": "https://openalex.org/W2776961836",
    "why_relevant": "Matched Figure 1 bibliographic search query '\"direct replication\" \"effect sizes\" \"dataset\"'; lead_classification=corpus_database_or_project_signal; score=17; reasons=strong_phrase:many labs | pair_term:original effect | pair_term:replication effect | pair_term:effect size | pair_term:cohen | replication_word | original_word"
  },
  {
    "inventory_status": "discovered_search_lead",
    "landing_url": "https://doi.org/10.1177/2515245918810225",
    "manifest_path": "steps/searches/figure1/corporasearch-citation-expanded-known-replication-databases.json",
    "name": "Many Labs 2: Investigating Variation in Replicability Across Samples and Settings",
    "next_action": "triage_landing_page_or_package_for_pair_table",
    "node_id": "node_search_manifest_edf033939b41",
    "node_source": "search_manifest",
    "record_kind": "candidate_corpus_or_database",
    "review_queue_status": "needs_root_candidate_review",
    "source_key": "https://openalex.org/W2776961836",
    "why_relevant": "Matched Figure 1 citation search query '\"Many Labs\" \"original study\"'; lead_classification=corpus_database_or_project_signal; score=17; reasons=strong_phrase:many labs | pair_term:original effect | pair_term:replication effect | pair_term:effect size | pair_term:cohen | replication_word | original_word"
  },
  {
    "inventory_status": "discovered_search_lead",
    "landing_url": "https://doi.org/10.1177/2515245918810225",
    "manifest_path": "steps/searches/figure1/corporasearch-citation-snowball-known-replication-corpora.json",
    "name": "Many Labs 2: Investigating Variation in Replicability Across Samples and Settings",
    "next_action": "triage_landing_page_or_package_for_pair_table",
    "node_id": "node_search_manifest_171530c954fe",
    "node_source": "search_manifest",
    "record_kind": "candidate_corpus_or_database",
    "review_queue_status": "needs_root_candidate_review",
    "source_key": "https://openalex.org/W2776961836",
    "why_relevant": "Matched Figure 1 citation search query '\"Many Labs\" replication project dataset'; lead_classification=corpus_database_or_project_signal; score=17; reasons=strong_phrase:many labs | pair_term:original effect | pair_term:replication effect | pair_term:effect size | pair_term:cohen | replication_word | original_word"
  },
  {
    "inventory_status": "discovered_search_lead",
    "landing_url": "https://doi.org/10.1177/2515245918810225",
    "manifest_path": "steps/searches/figure1/corporasearch-citation-snowball-known-replication-corpora.json",
    "name": "Many Labs 2: Investigating Variation in Replicability Across Samples and Settings",
    "next_action": "triage_landing_page_or_package_for_pair_table",
    "node_id": "node_search_manifest_b2319319c25c",
    "node_source": "search_manifest",
    "record_kind": "candidate_corpus_or_database",
    "review_queue_status": "needs_root_candidate_review",
    "source_key": "https://openalex.org/W2776961836",
    "why_relevant": "Matched Figure 1 citation search query '\"Social Science Replication Project\" dataset -> cites:W2886512263'; lead_classification=corpus_database_or_project_signal; score=17; reasons=strong_phrase:many labs | pair_term:original effect | pair_term:replication effect | pair_term:effect size | pair_term:cohen | replication_word | original_word"
  },
  {
    "inventory_status": "discovered_search_lead",
    "landing_url": "https://doi.org/10.1177/2515245918810225",
    "manifest_path": "steps/searches/figure1/corporasearch-linkgraph-expanded-known-corpus-paper-dois-to-datasets.json",
    "name": "Many Labs 2: Investigating Variation in Replicability Across Samples and Settings",
    "next_action": "triage_landing_page_or_package_for_pair_table",
    "node_id": "node_search_manifest_eaa4d8720ff5",
    "node_source": "search_manifest",
    "record_kind": "candidate_corpus_or_database",
    "review_queue_status": "needs_root_candidate_review",
    "source_key": "10.1177/2515245918810225",
    "why_relevant": "Matched Figure 1 link_graph search query '10.1038/s43588-025-00840-7'; lead_classification=corpus_database_or_project_signal; score=10; reasons=strong_phrase:many labs | known_corpus_paper_link_graph | query_phrase_in_text"
  }
]
```

## 4. Investigating the replicability of preclinical cancer biology.
- cluster_id: `cluster_investigating_the_replicability_of_preclinical_cancer_biology_ca7b83bfae6f`
- priority: `high / 97`
- confidence: `strict`
- preferred_family_hint: `rpcb`
- node_count: `6`; open_review_count: `6`; omitted_node_count: `0`
- strict_keys: `doi:10.7554/elife.71601 | url:https://doi.org/10.7554/elife.71601 | title:investigating_the_replicability_of_preclinical_cancer_biology`
- record_kind_counts: `{"candidate_corpus_or_database": 6}`
- inventory_status_counts: `{"discovered_search_lead": 6}`

Compact nodes:

```json
[
  {
    "inventory_status": "discovered_search_lead",
    "landing_url": "https://doi.org/10.7554/elife.71601",
    "manifest_path": "steps/searches/figure1/corporasearch-bibliographic-openalex-crossref-replication-database-effect-size.json | steps/searches/figure1/corporasearch-domain-multifield-replication-database-effect-size.json",
    "name": "Investigating the replicability of preclinical cancer biology.",
    "next_action": "triage_landing_page_or_package_for_pair_table",
    "node_id": "node_root_table_811621af6cb4",
    "node_source": "root_table",
    "record_kind": "candidate_corpus_or_database",
    "review_queue_status": "needs_root_candidate_review",
    "source_key": "PMC8651293 | https://openalex.org/W4200247206",
    "why_relevant": "Matched Figure 1 bibliographic search query '\"replication rates\" \"coded\" \"effect sizes\"'; lead_classification=corpus_database_or_project_signal; score=20; reasons=strong_phrase:reproducibility project | pair_term:original effect | pair_term:replication effect | pair_term:effect size | data_term:data | replication_word | original_word | effect_or_sample_size_phrase | metadata_corpus_signal"
  },
  {
    "inventory_status": "discovered_search_lead",
    "landing_url": "https://doi.org/10.7554/elife.71601",
    "manifest_path": "steps/searches/figure1/corporasearch-bibliographic-openalex-crossref-replication-database-effect-size.json",
    "name": "Investigating the replicability of preclinical cancer biology",
    "next_action": "triage_landing_page_or_package_for_pair_table",
    "node_id": "node_search_manifest_31e1fb8b7d64",
    "node_source": "search_manifest",
    "record_kind": "candidate_corpus_or_database",
    "review_queue_status": "needs_root_candidate_review",
    "source_key": "https://openalex.org/W4200247206",
    "why_relevant": "Matched Figure 1 bibliographic search query '\"reproducibility project\" \"effect sizes\"'; lead_classification=corpus_database_or_project_signal; score=20; reasons=strong_phrase:reproducibility project | pair_term:original effect | pair_term:replication effect | pair_term:effect size | data_term:data | replication_word | original_word | effect_or_sample_size_phrase | metadata_corpus_signal"
  },
  {
    "inventory_status": "discovered_search_lead",
    "landing_url": "https://doi.org/10.7554/elife.71601",
    "manifest_path": "steps/searches/figure1/corporasearch-citation-expanded-known-replication-databases.json",
    "name": "Investigating the replicability of preclinical cancer biology",
    "next_action": "triage_landing_page_or_package_for_pair_table",
    "node_id": "node_search_manifest_03465f6cb8a6",
    "node_source": "search_manifest",
    "record_kind": "candidate_corpus_or_database",
    "review_queue_status": "needs_root_candidate_review",
    "source_key": "https://openalex.org/W4200247206",
    "why_relevant": "Matched Figure 1 citation search query '\"Reproducibility Project: Cancer Biology\" \"effect size\"'; lead_classification=corpus_database_or_project_signal; score=20; reasons=strong_phrase:reproducibility project | pair_term:original effect | pair_term:replication effect | pair_term:effect size | data_term:data | replication_word | original_word | effect_or_sample_size_phrase | metadata_corpus_signal"
  },
  {
    "inventory_status": "discovered_search_lead",
    "landing_url": "https://doi.org/10.7554/elife.71601",
    "manifest_path": "steps/searches/figure1/corporasearch-citation-expanded-known-replication-databases.json",
    "name": "Investigating the replicability of preclinical cancer biology",
    "next_action": "triage_landing_page_or_package_for_pair_table",
    "node_id": "node_search_manifest_74ec80f56d40",
    "node_source": "search_manifest",
    "record_kind": "candidate_corpus_or_database",
    "review_queue_status": "needs_root_candidate_review",
    "source_key": "https://openalex.org/W4200247206",
    "why_relevant": "Matched Figure 1 citation search query '\"DARPA SCORE\" \"replication\" \"dataset\" -> cites:W3161588210'; lead_classification=corpus_database_or_project_signal; score=20; reasons=strong_phrase:reproducibility project | pair_term:original effect | pair_term:replication effect | pair_term:effect size | data_term:data | replication_word | original_word | effect_or_sample_size_phrase | metadata_corpus_signal"
  },
  {
    "inventory_status": "discovered_search_lead",
    "landing_url": "https://doi.org/10.7554/elife.71601",
    "manifest_path": "steps/searches/figure1/corporasearch-domain-multifield-replication-database-effect-size.json",
    "name": "Investigating the replicability of preclinical cancer biology",
    "next_action": "triage_landing_page_or_package_for_pair_table",
    "node_id": "node_search_manifest_b84cea913272",
    "node_source": "search_manifest",
    "record_kind": "candidate_corpus_or_database",
    "review_queue_status": "needs_root_candidate_review",
    "source_key": "https://openalex.org/W4200247206",
    "why_relevant": "Matched Figure 1 domain search query 'preclinical replication project effect size'; lead_classification=corpus_database_or_project_signal; score=20; reasons=strong_phrase:reproducibility project | pair_term:original effect | pair_term:replication effect | pair_term:effect size | data_term:data | replication_word | original_word | effect_or_sample_size_phrase | metadata_corpus_signal"
  },
  {
    "inventory_status": "discovered_search_lead",
    "landing_url": "https://doi.org/10.7554/elife.71601",
    "manifest_path": "steps/searches/figure1/corporasearch-bibliographic-openalex-crossref-replication-database-effect-size.json",
    "name": "Investigating the replicability of preclinical cancer biology.",
    "next_action": "triage_landing_page_or_package_for_pair_table",
    "node_id": "node_search_manifest_0fa048d165fd",
    "node_source": "search_manifest",
    "record_kind": "candidate_corpus_or_database",
    "review_queue_status": "needs_root_candidate_review",
    "source_key": "PMC8651293",
    "why_relevant": "Matched Figure 1 bibliographic search query '\"replication rates\" \"coded\" \"effect sizes\"'; lead_classification=corpus_database_or_project_signal; score=20; reasons=strong_phrase:reproducibility project | pair_term:original effect | pair_term:replication effect | pair_term:effect size | data_term:data | replication_word | original_word | effect_or_sample_size_phrase | metadata_corpus_signal"
  }
]
```

## 5. original results
- cluster_id: `cluster_original_results_6f97d3e8008c`
- priority: `high / 95`
- confidence: `strict`
- preferred_family_hint: ``
- node_count: `3`; open_review_count: `3`; omitted_node_count: `0`
- strict_keys: `raw_replication_project:decision_market`
- record_kind_counts: `{"candidate_result_table": 3}`
- inventory_status_counts: `{"needs_triage_search_lead": 3}`

Compact nodes:

```json
[
  {
    "inventory_status": "needs_triage_search_lead",
    "landing_url": "data/raw/replication_projects/decision_market/_codebook.md",
    "manifest_path": "steps/searches/figure1/corporasearch-code-expanded-local-pair-field-signatures.json",
    "name": "codebook",
    "next_action": "triage_file_for_pair_table_or_source_family",
    "node_id": "node_search_manifest_83d5a32ea989",
    "node_source": "search_manifest",
    "record_kind": "candidate_result_table",
    "review_queue_status": "needs_review",
    "source_key": "data/raw/replication_projects/decision_market/_codebook.md",
    "why_relevant": "Matched Figure 1 code search query 'study_pair_id original replication'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=14; reasons=strong_phrase:replication studies | pair_term:original study | data_term:data | data_term:code | replication_word | original_word | query_phrase_in_text"
  },
  {
    "inventory_status": "needs_triage_search_lead",
    "landing_url": "data/raw/replication_projects/decision_market/original_planned_samples.csv",
    "manifest_path": "steps/searches/figure1/corporasearch-code-expanded-local-pair-field-signatures.json",
    "name": "original planned samples",
    "next_action": "triage_file_for_pair_table_or_source_family",
    "node_id": "node_search_manifest_2bfefeee2bf7",
    "node_source": "search_manifest",
    "record_kind": "candidate_result_table",
    "review_queue_status": "needs_review",
    "source_key": "data/raw/replication_projects/decision_market/original_planned_samples.csv",
    "why_relevant": "Matched Figure 1 code search query 'study_pair_id original replication'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=9; reasons=data_term:data | replication_word | original_word | local_table_or_code_surface | query_phrase_in_text"
  },
  {
    "inventory_status": "needs_triage_search_lead",
    "landing_url": "data/raw/replication_projects/decision_market/original_results.csv",
    "manifest_path": "steps/searches/figure1/corporasearch-code-expanded-local-pair-field-signatures.json",
    "name": "original results",
    "next_action": "triage_file_for_pair_table_or_source_family",
    "node_id": "node_search_manifest_2b84fa6f9225",
    "node_source": "search_manifest",
    "record_kind": "candidate_result_table",
    "review_queue_status": "needs_review",
    "source_key": "data/raw/replication_projects/decision_market/original_results.csv",
    "why_relevant": "Matched Figure 1 code search query 'study_pair_id original replication'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=9; reasons=data_term:data | replication_word | original_word | local_table_or_code_surface | query_phrase_in_text"
  }
]
```

## 6. create studydetails
- cluster_id: `cluster_create_studydetails_815faf854db4`
- priority: `high / 94`
- confidence: `strict`
- preferred_family_hint: ``
- node_count: `3`; open_review_count: `3`; omitted_node_count: `0`
- strict_keys: `raw_replication_project:eerp`
- record_kind_counts: `{"candidate_result_table": 3}`
- inventory_status_counts: `{"needs_triage_search_lead": 3}`

Compact nodes:

```json
[
  {
    "inventory_status": "needs_triage_search_lead",
    "landing_url": "data/raw/replication_projects/eerp/create_studydetails.do",
    "manifest_path": "steps/searches/figure1/corporasearch-code-expanded-local-pair-field-signatures.json",
    "name": "create studydetails",
    "next_action": "triage_file_for_pair_table_or_source_family",
    "node_id": "node_search_manifest_9c0a33f3b974",
    "node_source": "search_manifest",
    "record_kind": "candidate_result_table",
    "review_queue_status": "needs_review",
    "source_key": "data/raw/replication_projects/eerp/create_studydetails.do",
    "why_relevant": "Matched Figure 1 code search query 'study_pair_id original replication'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=9; reasons=pair_term:original study | data_term:data | data_term:code | replication_word | original_word | query_phrase_in_text"
  },
  {
    "inventory_status": "needs_triage_search_lead",
    "landing_url": "data/raw/replication_projects/eerp/effectstandardization.py",
    "manifest_path": "steps/searches/figure1/corporasearch-code-expanded-local-pair-field-signatures.json",
    "name": "effectstandardization",
    "next_action": "triage_file_for_pair_table_or_source_family",
    "node_id": "node_search_manifest_09b11a326972",
    "node_source": "search_manifest",
    "record_kind": "candidate_result_table",
    "review_queue_status": "needs_review",
    "source_key": "data/raw/replication_projects/eerp/effectstandardization.py",
    "why_relevant": "Matched Figure 1 code search query 'study_pair_id original replication'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=7; reasons=data_term:data | data_term:code | replication_word | original_word | query_phrase_in_text"
  },
  {
    "inventory_status": "needs_triage_search_lead",
    "landing_url": "data/raw/replication_projects/eerp/marketdata_extracted/Stata/raw/rpp_data.csv",
    "manifest_path": "steps/searches/figure1/corporasearch-code-expanded-local-pair-field-signatures.json",
    "name": "rpp data",
    "next_action": "triage_file_for_pair_table_or_source_family",
    "node_id": "node_search_manifest_385686ba8a5c",
    "node_source": "search_manifest",
    "record_kind": "candidate_result_table",
    "review_queue_status": "needs_review",
    "source_key": "data/raw/replication_projects/eerp/marketdata_extracted/Stata/raw/rpp_data.csv",
    "why_relevant": "Matched Figure 1 code search query 'study_pair_id original replication'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=11; reasons=pair_term:original study | data_term:data | replication_word | original_word | local_table_or_code_surface | query_phrase_in_text"
  }
]
```

## 7. Political Science Unlock
- cluster_id: `cluster_political_science_unlock_51f64b60725b`
- priority: `high / 94`
- confidence: `strict`
- preferred_family_hint: `fred`
- node_count: `85`; open_review_count: `51`; omitted_node_count: `73`
- strict_keys: `raw_corpus:political_science_unlock | title:minimal_effects_online_appendix`
- record_kind_counts: `{"candidate_individual_paper_or_package": 1, "candidate_result_table": 57, "corpus_or_database": 26, "raw_inventory_dir": 1}`
- inventory_status_counts: `{"included": 26, "needs_triage_search_lead": 57, "raw_available": 1, "routed_to_individual_paper_search": 1}`

Compact nodes:

```json
[
  {
    "inventory_status": "needs_triage_search_lead",
    "landing_url": "data/raw/corpus_candidates/political_science_unlock/dataverse_metadata/3VVWPL.json",
    "manifest_path": "steps/searches/figure1/corporasearch-code-expanded-local-pair-field-signatures.json",
    "name": "3VVWPL",
    "next_action": "triage_file_for_pair_table_or_source_family",
    "node_id": "node_search_manifest_0f7fd49caed3",
    "node_source": "search_manifest",
    "record_kind": "candidate_result_table",
    "review_queue_status": "needs_review",
    "source_key": "data/raw/corpus_candidates/political_science_unlock/dataverse_metadata/3VVWPL.json",
    "why_relevant": "Matched Figure 1 code search query 'study_pair_id original replication'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=10; reasons=data_term:data | data_term:dataverse | replication_word | original_word | local_table_or_code_surface | query_phrase_in_text"
  },
  {
    "inventory_status": "needs_triage_search_lead",
    "landing_url": "data/raw/corpus_candidates/political_science_unlock/dataverse_metadata/3VVWPL.json",
    "manifest_path": "steps/searches/figure1/corporasearch-code-local-original-replication-fields.json",
    "name": "3VVWPL",
    "next_action": "triage_file_for_pair_table_or_source_family",
    "node_id": "node_search_manifest_a5f12ec58c71",
    "node_source": "search_manifest",
    "record_kind": "candidate_result_table",
    "review_queue_status": "needs_review",
    "source_key": "data/raw/corpus_candidates/political_science_unlock/dataverse_metadata/3VVWPL.json",
    "why_relevant": "Matched Figure 1 code search query 'effect_size sample_size original replication'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=10; reasons=data_term:data | data_term:dataverse | replication_word | original_word | local_table_or_code_surface | query_phrase_in_text"
  },
  {
    "inventory_status": "needs_triage_search_lead",
    "landing_url": "data/raw/corpus_candidates/political_science_unlock/dataverse/9PWQZT/4_an_ps.R",
    "manifest_path": "steps/searches/figure1/corporasearch-code-local-original-replication-fields.json",
    "name": "4 an ps",
    "next_action": "triage_file_for_pair_table_or_source_family",
    "node_id": "node_search_manifest_d9abe2ad72a8",
    "node_source": "search_manifest",
    "record_kind": "candidate_result_table",
    "review_queue_status": "needs_review",
    "source_key": "data/raw/corpus_candidates/political_science_unlock/dataverse/9PWQZT/4_an_ps.R",
    "why_relevant": "Matched Figure 1 code search query 'paired replication table'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=9; reasons=data_term:data | data_term:code | data_term:dataverse | replication_word | local_table_or_code_surface | query_phrase_in_text"
  },
  {
    "inventory_status": "needs_triage_search_lead",
    "landing_url": "data/raw/corpus_candidates/political_science_unlock/dataverse/RAMHWP/4_meta_analysis_code.R",
    "manifest_path": "steps/searches/figure1/corporasearch-code-local-original-replication-fields.json",
    "name": "4 meta analysis code",
    "next_action": "triage_file_for_pair_table_or_source_family",
    "node_id": "node_search_manifest_52ee7cd58dc6",
    "node_source": "search_manifest",
    "record_kind": "candidate_result_table",
    "review_queue_status": "needs_review",
    "source_key": "data/raw/corpus_candidates/political_science_unlock/dataverse/RAMHWP/4_meta_analysis_code.R",
    "why_relevant": "Matched Figure 1 code search query 'effect_size sample_size original replication'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=8; reasons=data_term:data | data_term:code | data_term:dataverse | replication_word | original_word | query_phrase_in_text"
  },
  {
    "inventory_status": "needs_triage_search_lead",
    "landing_url": "data/raw/corpus_candidates/political_science_unlock/dataverse_metadata/5OPIYU.json",
    "manifest_path": "steps/searches/figure1/corporasearch-code-local-original-replication-fields.json",
    "name": "5OPIYU",
    "next_action": "triage_file_for_pair_table_or_source_family",
    "node_id": "node_search_manifest_206085cb85a0",
    "node_source": "search_manifest",
    "record_kind": "candidate_result_table",
    "review_queue_status": "needs_review",
    "source_key": "data/raw/corpus_candidates/political_science_unlock/dataverse_metadata/5OPIYU.json",
    "why_relevant": "Matched Figure 1 code search query 'direct_replication dataset'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=7; reasons=data_term:data | data_term:dataset | data_term:dataverse | local_table_or_code_surface | query_phrase_in_text"
  },
  {
    "inventory_status": "routed_to_individual_paper_search",
    "landing_url": "data/raw/corpus_candidates/political_science_unlock/dataverse/OJA7YS/BKO_Debates_Replication_Code.do",
    "manifest_path": "steps/searches/figure1/corporasearch-code-local-original-replication-fields.json",
    "name": "BKO Debates Replication Code",
    "next_action": "route_to_individual_replication_paper_worklist",
    "node_id": "node_search_manifest_8f6399028a15",
    "node_source": "search_manifest",
    "record_kind": "candidate_individual_paper_or_package",
    "review_queue_status": "needs_review",
    "source_key": "data/raw/corpus_candidates/political_science_unlock/dataverse/OJA7YS/BKO_Debates_Replication_Code.do",
    "why_relevant": "Matched Figure 1 code search query 'paired replication table'; lead_classification=individual_paper_or_one_off_package_signal; score=9; reasons=data_term:data | data_term:code | data_term:dataverse | replication_word | local_table_or_code_surface | query_phrase_in_text"
  },
  {
    "inventory_status": "needs_triage_search_lead",
    "landing_url": "data/raw/corpus_candidates/political_science_unlock/github/Direct-Aid-Replication-Materials/Replication Materials/Code/CostEffCalculations.xlsx",
    "manifest_path": "steps/searches/figure1/corporasearch-code-local-original-replication-fields.json",
    "name": "CostEffCalculations",
    "next_action": "triage_file_for_pair_table_or_source_family",
    "node_id": "node_search_manifest_b4f301a5707b",
    "node_source": "search_manifest",
    "record_kind": "candidate_result_table",
    "review_queue_status": "needs_review",
    "source_key": "data/raw/corpus_candidates/political_science_unlock/github/Direct-Aid-Replication-Materials/Replication Materials/Code/CostEffCalculations.xlsx",
    "why_relevant": "Matched Figure 1 code search query 'effect_size sample_size original replication'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=10; reasons=data_term:data | data_term:code | replication_word | original_word | local_table_or_code_surface | query_phrase_in_text"
  },
  {
    "inventory_status": "needs_triage_search_lead",
    "landing_url": "data/raw/corpus_candidates/political_science_unlock/github/Direct-Aid-Replication-Materials/Replication Materials/Code/Figure_3.do",
    "manifest_path": "steps/searches/figure1/corporasearch-code-expanded-local-pair-field-signatures.json",
    "name": "Figure 3",
    "next_action": "triage_file_for_pair_table_or_source_family",
    "node_id": "node_search_manifest_726b0a8b6928",
    "node_source": "search_manifest",
    "record_kind": "candidate_result_table",
    "review_queue_status": "needs_review",
    "source_key": "data/raw/corpus_candidates/political_science_unlock/github/Direct-Aid-Replication-Materials/Replication Materials/Code/Figure_3.do",
    "why_relevant": "Matched Figure 1 code search query 'study_pair_id original replication'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=7; reasons=data_term:data | data_term:code | replication_word | original_word | query_phrase_in_text"
  },
  {
    "inventory_status": "needs_triage_search_lead",
    "landing_url": "data/raw/corpus_candidates/political_science_unlock/github/Direct-Aid-Replication-Materials/Replication Materials/Code/Figure_3.do",
    "manifest_path": "steps/searches/figure1/corporasearch-code-local-original-replication-fields.json",
    "name": "Figure 3",
    "next_action": "triage_file_for_pair_table_or_source_family",
    "node_id": "node_search_manifest_49b65f46c605",
    "node_source": "search_manifest",
    "record_kind": "candidate_result_table",
    "review_queue_status": "needs_review",
    "source_key": "data/raw/corpus_candidates/political_science_unlock/github/Direct-Aid-Replication-Materials/Replication Materials/Code/Figure_3.do",
    "why_relevant": "Matched Figure 1 code search query 'effect_size sample_size original replication'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=7; reasons=data_term:data | data_term:code | replication_word | original_word | query_phrase_in_text"
  },
  {
    "inventory_status": "needs_triage_search_lead",
    "landing_url": "data/raw/corpus_candidates/political_science_unlock/dataverse/R75XVZ/Master.do",
    "manifest_path": "steps/searches/figure1/corporasearch-code-local-original-replication-fields.json",
    "name": "Master",
    "next_action": "triage_file_for_pair_table_or_source_family",
    "node_id": "node_search_manifest_324acf815000",
    "node_source": "search_manifest",
    "record_kind": "candidate_result_table",
    "review_queue_status": "needs_review",
    "source_key": "data/raw/corpus_candidates/political_science_unlock/dataverse/R75XVZ/Master.do",
    "why_relevant": "Matched Figure 1 code search query 'paired replication table'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=9; reasons=data_term:data | data_term:code | data_term:dataverse | replication_word | local_table_or_code_surface | query_phrase_in_text"
  },
  {
    "inventory_status": "needs_triage_search_lead",
    "landing_url": "data/raw/corpus_candidates/political_science_unlock/dataverse/RAMHWP/Minimal_Effects_Online_Appendix.Rmd",
    "manifest_path": "steps/searches/figure1/corporasearch-code-expanded-local-pair-field-signatures.json",
    "name": "Minimal Effects Online Appendix",
    "next_action": "triage_file_for_pair_table_or_source_family",
    "node_id": "node_search_manifest_f5dd95254e79",
    "node_source": "search_manifest",
    "record_kind": "candidate_result_table",
    "review_queue_status": "needs_review",
    "source_key": "data/raw/corpus_candidates/political_science_unlock/dataverse/RAMHWP/Minimal_Effects_Online_Appendix.Rmd",
    "why_relevant": "Matched Figure 1 code search query 'study_pair_id original replication'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=8; reasons=data_term:data | data_term:code | data_term:dataverse | replication_word | original_word | query_phrase_in_text"
  },
  {
    "inventory_status": "needs_triage_search_lead",
    "landing_url": "data/raw/corpus_candidates/political_science_unlock/dataverse/RAMHWP/Minimal_Effects_Online_Appendix.Rmd",
    "manifest_path": "steps/searches/figure1/corporasearch-code-local-original-replication-fields.json",
    "name": "Minimal Effects Online Appendix",
    "next_action": "triage_file_for_pair_table_or_source_family",
    "node_id": "node_search_manifest_111365ff0d12",
    "node_source": "search_manifest",
    "record_kind": "candidate_result_table",
    "review_queue_status": "needs_review",
    "source_key": "data/raw/corpus_candidates/political_science_unlock/dataverse/RAMHWP/Minimal_Effects_Online_Appendix.Rmd",
    "why_relevant": "Matched Figure 1 code search query 'effect_size sample_size original replication'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=8; reasons=data_term:data | data_term:code | data_term:dataverse | replication_word | original_word | query_phrase_in_text"
  }
]
```

## 8. 004 codebook
- cluster_id: `cluster_004_codebook_8eae1835c41b`
- priority: `high / 93`
- confidence: `strict`
- preferred_family_hint: ``
- node_count: `3`; open_review_count: `3`; omitted_node_count: `0`
- strict_keys: `lead_harvest:psa_004_turri`
- record_kind_counts: `{"candidate_result_table": 3}`
- inventory_status_counts: `{"needs_triage_search_lead": 3}`

Compact nodes:

```json
[
  {
    "inventory_status": "needs_triage_search_lead",
    "landing_url": "data/raw/replication_projects/lead_harvest/psa_004_turri/osf_erm92/004_codebook.xlsx",
    "manifest_path": "steps/searches/figure1/corporasearch-code-expanded-local-pair-field-signatures.json",
    "name": "004 codebook",
    "next_action": "triage_file_for_pair_table_or_source_family",
    "node_id": "node_search_manifest_068a55aa5aa4",
    "node_source": "search_manifest",
    "record_kind": "candidate_result_table",
    "review_queue_status": "needs_review",
    "source_key": "data/raw/replication_projects/lead_harvest/psa_004_turri/osf_erm92/004_codebook.xlsx",
    "why_relevant": "Matched Figure 1 code search query 'study_pair_id original replication'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=11; reasons=data_term:data | data_term:code | data_term:osf | replication_word | original_word | local_table_or_code_surface | query_phrase_in_text"
  },
  {
    "inventory_status": "needs_triage_search_lead",
    "landing_url": "data/raw/replication_projects/lead_harvest/psa_004_turri/osf_n5b3w_full/pretest script.R",
    "manifest_path": "steps/searches/figure1/corporasearch-code-expanded-local-pair-field-signatures.json",
    "name": "pretest script",
    "next_action": "triage_file_for_pair_table_or_source_family",
    "node_id": "node_search_manifest_9b22ad70869a",
    "node_source": "search_manifest",
    "record_kind": "candidate_result_table",
    "review_queue_status": "needs_review",
    "source_key": "data/raw/replication_projects/lead_harvest/psa_004_turri/osf_n5b3w_full/pretest script.R",
    "why_relevant": "Matched Figure 1 code search query 'study_pair_id original replication'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=8; reasons=data_term:data | data_term:code | data_term:osf | replication_word | original_word | query_phrase_in_text"
  },
  {
    "inventory_status": "needs_triage_search_lead",
    "landing_url": "data/raw/replication_projects/lead_harvest/psa_004_turri/psa004_turri_article_table_reconstruction.csv",
    "manifest_path": "steps/searches/figure1/corporasearch-code-expanded-local-pair-field-signatures.json",
    "name": "psa004 turri article table reconstruction",
    "next_action": "triage_file_for_pair_table_or_source_family",
    "node_id": "node_search_manifest_b6dd284713b7",
    "node_source": "search_manifest",
    "record_kind": "candidate_result_table",
    "review_queue_status": "needs_review",
    "source_key": "data/raw/replication_projects/lead_harvest/psa_004_turri/psa004_turri_article_table_reconstruction.csv",
    "why_relevant": "Matched Figure 1 code search query 'original_n replication_n'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=5; reasons=data_term:data | local_table_or_code_surface | query_phrase_in_text"
  }
]
```
