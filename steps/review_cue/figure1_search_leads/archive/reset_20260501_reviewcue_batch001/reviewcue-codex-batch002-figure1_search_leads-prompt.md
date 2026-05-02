# figure1_search_leads Codex Review Prompt

Save returned JSON as `steps/review_cue/figure1_search_leads/reviewcue-decisions-figure1_search_leads-codex-batch002.json`.

```text
You are a Codex background reviewer for review cue `figure1_search_leads`.
Reusable bounded review queue for ambiguous Figure 1 corpus/database, repository-package, result-table, individual-paper, and context-source leads. Deterministic scripts should remove obvious duplicates and false positives first. Codex should investigate moderate batches and either make auditable decisions or emit compact GPT prompt requests for uncertain cases. GPT prompt batches can be larger because they are user-mediated review artifacts.

Work only this bounded batch. Investigate URLs and source metadata when useful.
Do not edit root tables. Return or save JSON decisions using the contract below.
Each accepted decision will later be applied as a per-lead receipt file, so future cue builds can skip it by checking for that target file.
If you are not confident, set decision to `needs_more_evidence` and include `user_gpt_prompt_request` with a compact prompt the user can give to GPT Pro.

Save decisions as: `steps/review_cue/figure1_search_leads/reviewcue-decisions-figure1_search_leads-codex-batch002.json`

Allowed decisions:
- keep_in_corpora_and_databases
- promote_to_corpora_and_databases
- route_to_result_table_worklist
- route_to_individual_replication_paper_worklist
- keep_as_context_source
- reject_irrelevant
- needs_more_evidence

Each decision requires:
review_id, lead_key, decision, confidence, reason, next_action

Decision-specific requirements:
{
  "route_to_individual_replication_paper_worklist": {
    "allowed_replication_relation_evidence_status": [
      "explicit_self_described_replication",
      "metadata_links_original_and_replication",
      "source_contains_pair_mapping"
    ],
    "reject_if": "The source is merely an individual pilot, feasibility study, ordinary trial, paper, or package with no affirmative evidence that it is itself a replication/reproduction/follow-up of an identifiable original. Do not route something forward because a later larger study might exist.\n",
    "required_route_payload_fields": [
      "replication_relation_evidence_status",
      "replication_relation_evidence"
    ]
  }
}

Return JSON in this shape:
{"decisions": [{"review_id": "...", "lead_key": "...", "decision": "...", "confidence": "high|medium|low", "reason": "...", "next_action": "...", "sources_checked": [], "promote_payload": {}, "route_payload": {}, "user_gpt_prompt_request": ""}]}

Leads:
1. review_id: review_figure1_search_leads_2d583bbe453b
   lead_key: title:3vvwpl
   queue_status: needs_review
   name: 3VVWPL
   record_kind: candidate_result_table
   inventory_status: needs_triage_search_lead
   url: data/raw/corpus_candidates/political_science_unlock/dataverse_metadata/3VVWPL.json
   source_key: data/raw/corpus_candidates/political_science_unlock/dataverse_metadata/3VVWPL.json
   description: Local scan hit; file_type=table_or_package; matched_query=effect_size sample_size original replication; path=data/raw/corpus_candidates/political_science_unlock/dataverse_metadata/3VVWPL.json; snippet=
   current heuristic reason: Matched Figure 1 code search query 'effect_size sample_size original replication'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=10; reasons=data_term:data | data_term:dataverse | replication_word | original_word | local_table_or_code_surface | query_phrase_in_text

2. review_id: review_figure1_search_leads_62dbd49f5187
   lead_key: title:4_an_ps
   queue_status: needs_review
   name: 4 an ps
   record_kind: candidate_result_table
   inventory_status: needs_triage_search_lead
   url: data/raw/corpus_candidates/political_science_unlock/dataverse/9PWQZT/4_an_ps.R
   source_key: data/raw/corpus_candidates/political_science_unlock/dataverse/9PWQZT/4_an_ps.R
   description: Local scan hit; file_type=text_or_code; matched_query=paired replication table; path=data/raw/corpus_candidates/political_science_unlock/dataverse/9PWQZT/4_an_ps.R; snippet=
   current heuristic reason: Matched Figure 1 code search query 'paired replication table'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=9; reasons=data_term:data | data_term:code | data_term:dataverse | replication_word | local_table_or_code_surface | query_phrase_in_text

3. review_id: review_figure1_search_leads_f2f651645c0a
   lead_key: title:4_meta_analysis_code
   queue_status: needs_review
   name: 4 meta analysis code
   record_kind: candidate_result_table
   inventory_status: needs_triage_search_lead
   url: data/raw/corpus_candidates/political_science_unlock/dataverse/RAMHWP/4_meta_analysis_code.R
   source_key: data/raw/corpus_candidates/political_science_unlock/dataverse/RAMHWP/4_meta_analysis_code.R
   description: Local scan hit; file_type=text_or_code; matched_query=effect_size sample_size original replication; path=data/raw/corpus_candidates/political_science_unlock/dataverse/RAMHWP/4_meta_analysis_code.R; snippet=
   current heuristic reason: Matched Figure 1 code search query 'effect_size sample_size original replication'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=8; reasons=data_term:data | data_term:code | data_term:dataverse | replication_word | original_word | query_phrase_in_text

4. review_id: review_figure1_search_leads_985f3099c6b1
   lead_key: title:5opiyu
   queue_status: needs_review
   name: 5OPIYU
   record_kind: candidate_result_table
   inventory_status: needs_triage_search_lead
   url: data/raw/corpus_candidates/political_science_unlock/dataverse_metadata/5OPIYU.json
   source_key: data/raw/corpus_candidates/political_science_unlock/dataverse_metadata/5OPIYU.json
   description: Local scan hit; file_type=table_or_package; matched_query=direct_replication dataset; path=data/raw/corpus_candidates/political_science_unlock/dataverse_metadata/5OPIYU.json; snippet=
   current heuristic reason: Matched Figure 1 code search query 'direct_replication dataset'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=7; reasons=data_term:data | data_term:dataset | data_term:dataverse | local_table_or_code_surface | query_phrase_in_text

5. review_id: review_figure1_search_leads_82a4535f8d2c
   lead_key: title:add_metalab_summary
   queue_status: needs_review
   name: add metalab summary
   record_kind: candidate_result_table
   inventory_status: needs_triage_search_lead
   url: data/raw/corpus_candidates/metalab/metalabr/R/add_metalab_summary.R
   source_key: data/raw/corpus_candidates/metalab/metalabr/R/add_metalab_summary.R
   description: Local scan hit; file_type=text_or_code; matched_query=direct_replication dataset; path=data/raw/corpus_candidates/metalab/metalabr/R/add_metalab_summary.R; snippet=
   current heuristic reason: Matched Figure 1 code search query 'direct_replication dataset'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=4; reasons=data_term:data | data_term:dataset | data_term:code | query_phrase_in_text

6. review_id: review_figure1_search_leads_1dbd556a488d
   lead_key: title:aea_dataverse_metadata
   queue_status: needs_review
   name: aea dataverse metadata
   record_kind: candidate_result_table
   inventory_status: needs_triage_search_lead
   url: data/raw/corpus_candidates/political_science_unlock/aea_dataverse_metadata.json
   source_key: data/raw/corpus_candidates/political_science_unlock/aea_dataverse_metadata.json
   description: Local scan hit; file_type=table_or_package; matched_query=direct_replication dataset; path=data/raw/corpus_candidates/political_science_unlock/aea_dataverse_metadata.json; snippet=
   current heuristic reason: Matched Figure 1 code search query 'direct_replication dataset'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=7; reasons=data_term:data | data_term:dataset | data_term:dataverse | local_table_or_code_surface | query_phrase_in_text

7. review_id: review_figure1_search_leads_7149b2d21d68
   lead_key: title:analyses_study_1
   queue_status: needs_review
   name: Analyses - Study 1
   record_kind: candidate_result_table
   inventory_status: needs_triage_search_lead
   url: data/raw/corpus_candidates/linden_2024/Analyses - Study 1.json
   source_key: data/raw/corpus_candidates/linden_2024/Analyses - Study 1.json
   description: Local scan hit; file_type=table_or_package; matched_query=effect_size sample_size original replication; path=data/raw/corpus_candidates/linden_2024/Analyses - Study 1.json; snippet="id": "656dd67202fa961c027d2862", "type": "files", "attributes": { "guid": "5ajs3", "checkout": null, "name": "correlation_effect_size_sample_size_meta_analyses_revision.html", "kind": "file", "path": "/656dd67202fa961c027d2862", "size": 3124152, "provider": "osfstorage",
   current heuristic reason: Matched Figure 1 code search query 'effect_size sample_size original replication'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=10; reasons=data_term:data | data_term:osf | replication_word | original_word | local_table_or_code_surface | query_phrase_in_text

8. review_id: review_figure1_search_leads_a75734217263
   lead_key: title:analysis
   queue_status: needs_review
   name: analysis
   record_kind: candidate_result_table
   inventory_status: needs_triage_search_lead
   url: data/raw/corpus_candidates/political_science_unlock/github/baraza/sc_report/analysis.R | data/raw/corpus_candidates/aczel_2018/analysis.Rmd | data/raw/corpus_candidates/schimmack_bartos_y3gae/re-analysis/analysis.R
   source_key: data/raw/corpus_candidates/political_science_unlock/github/baraza/sc_report/analysis.R | data/raw/corpus_candidates/aczel_2018/analysis.Rmd | data/raw/corpus_candidates/schimmack_bartos_y3gae/re-analysis/analysis.R
   description: Local scan hit; file_type=text_or_code; matched_query=paired replication table; path=data/raw/corpus_candidates/political_science_unlock/github/baraza/sc_report/analysis.R; snippet=
   current heuristic reason: Matched Figure 1 code search query 'paired replication table'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=8; reasons=data_term:data | data_term:code | replication_word | local_table_or_code_surface | query_phrase_in_text

9. review_id: review_figure1_search_leads_11edcc8f4b00
   lead_key: title:analysis_manuscript
   queue_status: needs_review
   name: analysis manuscript
   record_kind: candidate_result_table
   inventory_status: needs_triage_search_lead
   url: data/raw/corpus_candidates/political_science_unlock/dataverse/ETUUOD/analysis_manuscript.html
   source_key: data/raw/corpus_candidates/political_science_unlock/dataverse/ETUUOD/analysis_manuscript.html
   description: Local scan hit; file_type=text_or_code; matched_query=effect_size sample_size original replication; path=data/raw/corpus_candidates/political_science_unlock/dataverse/ETUUOD/analysis_manuscript.html; snippet=
   current heuristic reason: Matched Figure 1 code search query 'effect_size sample_size original replication'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=8; reasons=data_term:data | data_term:code | data_term:dataverse | replication_word | original_word | query_phrase_in_text

10. review_id: review_figure1_search_leads_6017a70ba1ee
   lead_key: title:analysis_report
   queue_status: needs_review
   name: analysis report
   record_kind: candidate_result_table
   inventory_status: needs_triage_search_lead
   url: data/raw/corpus_candidates/political_science_unlock/github/baraza/report/analysis_report.R
   source_key: data/raw/corpus_candidates/political_science_unlock/github/baraza/report/analysis_report.R
   description: Local scan hit; file_type=text_or_code; matched_query=direct_replication dataset; path=data/raw/corpus_candidates/political_science_unlock/github/baraza/report/analysis_report.R; snippet=
   current heuristic reason: Matched Figure 1 code search query 'direct_replication dataset'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=4; reasons=data_term:data | data_term:dataset | data_term:code | query_phrase_in_text

11. review_id: review_figure1_search_leads_f9353d2a3a81
   lead_key: title:analysis_report_additional
   queue_status: needs_review
   name: analysis report additional
   record_kind: candidate_result_table
   inventory_status: needs_triage_search_lead
   url: data/raw/corpus_candidates/political_science_unlock/github/baraza/report/analysis_report_additional.R
   source_key: data/raw/corpus_candidates/political_science_unlock/github/baraza/report/analysis_report_additional.R
   description: Local scan hit; file_type=text_or_code; matched_query=direct_replication dataset; path=data/raw/corpus_candidates/political_science_unlock/github/baraza/report/analysis_report_additional.R; snippet=
   current heuristic reason: Matched Figure 1 code search query 'direct_replication dataset'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=4; reasons=data_term:data | data_term:dataset | data_term:code | query_phrase_in_text

12. review_id: review_figure1_search_leads_5d91dbca8156
   lead_key: title:analysis_report_details
   queue_status: needs_review
   name: analysis report details
   record_kind: candidate_result_table
   inventory_status: needs_triage_search_lead
   url: data/raw/corpus_candidates/political_science_unlock/github/baraza/report/analysis_report_details.R
   source_key: data/raw/corpus_candidates/political_science_unlock/github/baraza/report/analysis_report_details.R
   description: Local scan hit; file_type=text_or_code; matched_query=direct_replication dataset; path=data/raw/corpus_candidates/political_science_unlock/github/baraza/report/analysis_report_details.R; snippet=
   current heuristic reason: Matched Figure 1 code search query 'direct_replication dataset'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=4; reasons=data_term:data | data_term:dataset | data_term:code | query_phrase_in_text

13. review_id: review_figure1_search_leads_ccadc817c181
   lead_key: title:analysis_report_dif_in_dif
   queue_status: needs_review
   name: analysis report dif in dif
   record_kind: candidate_result_table
   inventory_status: needs_triage_search_lead
   url: data/raw/corpus_candidates/political_science_unlock/github/baraza/report/analysis_report_dif_in_dif.R
   source_key: data/raw/corpus_candidates/political_science_unlock/github/baraza/report/analysis_report_dif_in_dif.R
   description: Local scan hit; file_type=text_or_code; matched_query=direct_replication dataset; path=data/raw/corpus_candidates/political_science_unlock/github/baraza/report/analysis_report_dif_in_dif.R; snippet=
   current heuristic reason: Matched Figure 1 code search query 'direct_replication dataset'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=4; reasons=data_term:data | data_term:dataset | data_term:code | query_phrase_in_text

14. review_id: review_figure1_search_leads_57c0a21e83ed
   lead_key: title:analysis_report_hetero_1
   queue_status: needs_review
   name: analysis report hetero 1
   record_kind: candidate_result_table
   inventory_status: needs_triage_search_lead
   url: data/raw/corpus_candidates/political_science_unlock/github/baraza/report/analysis_report_hetero_1.R
   source_key: data/raw/corpus_candidates/political_science_unlock/github/baraza/report/analysis_report_hetero_1.R
   description: Local scan hit; file_type=text_or_code; matched_query=direct_replication dataset; path=data/raw/corpus_candidates/political_science_unlock/github/baraza/report/analysis_report_hetero_1.R; snippet=
   current heuristic reason: Matched Figure 1 code search query 'direct_replication dataset'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=4; reasons=data_term:data | data_term:dataset | data_term:code | query_phrase_in_text

15. review_id: review_figure1_search_leads_22f41d4b2418
   lead_key: title:analysis_report_hetero_2
   queue_status: needs_review
   name: analysis report hetero 2
   record_kind: candidate_result_table
   inventory_status: needs_triage_search_lead
   url: data/raw/corpus_candidates/political_science_unlock/github/baraza/report/analysis_report_hetero_2.R
   source_key: data/raw/corpus_candidates/political_science_unlock/github/baraza/report/analysis_report_hetero_2.R
   description: Local scan hit; file_type=text_or_code; matched_query=direct_replication dataset; path=data/raw/corpus_candidates/political_science_unlock/github/baraza/report/analysis_report_hetero_2.R; snippet=
   current heuristic reason: Matched Figure 1 code search query 'direct_replication dataset'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=4; reasons=data_term:data | data_term:dataset | data_term:code | query_phrase_in_text

16. review_id: review_figure1_search_leads_9945c8a32405
   lead_key: title:analysis_report_interaction_time
   queue_status: needs_review
   name: analysis report interaction time
   record_kind: candidate_result_table
   inventory_status: needs_triage_search_lead
   url: data/raw/corpus_candidates/political_science_unlock/github/baraza/report/analysis_report_interaction_time.R
   source_key: data/raw/corpus_candidates/political_science_unlock/github/baraza/report/analysis_report_interaction_time.R
   description: Local scan hit; file_type=text_or_code; matched_query=direct_replication dataset; path=data/raw/corpus_candidates/political_science_unlock/github/baraza/report/analysis_report_interaction_time.R; snippet=
   current heuristic reason: Matched Figure 1 code search query 'direct_replication dataset'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=4; reasons=data_term:data | data_term:dataset | data_term:code | query_phrase_in_text

17. review_id: review_figure1_search_leads_c57909012c5a
   lead_key: title:analysis_report_matcher_details
   queue_status: needs_review
   name: analysis report matcher details
   record_kind: candidate_result_table
   inventory_status: needs_triage_search_lead
   url: data/raw/corpus_candidates/political_science_unlock/github/baraza/report/analysis_report_matcher_details.R
   source_key: data/raw/corpus_candidates/political_science_unlock/github/baraza/report/analysis_report_matcher_details.R
   description: Local scan hit; file_type=text_or_code; matched_query=direct_replication dataset; path=data/raw/corpus_candidates/political_science_unlock/github/baraza/report/analysis_report_matcher_details.R; snippet=
   current heuristic reason: Matched Figure 1 code search query 'direct_replication dataset'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=4; reasons=data_term:data | data_term:dataset | data_term:code | query_phrase_in_text

18. review_id: review_figure1_search_leads_74cd84ff553b
   lead_key: title:annotated_rct_dataset
   queue_status: needs_review
   name: annotated rct dataset
   record_kind: candidate_result_table
   inventory_status: needs_triage_search_lead
   url: data/raw/corpus_candidates/yun_llm_meta_analysis/llm-meta-analysis/evaluation/data/annotated_rct_dataset.csv | data/raw/corpus_candidates/yun_llm_meta_analysis/llm-meta-analysis/evaluation/data/annotated_rct_dataset.json
   source_key: data/raw/corpus_candidates/yun_llm_meta_analysis/llm-meta-analysis/evaluation/data/annotated_rct_dataset.csv | data/raw/corpus_candidates/yun_llm_meta_analysis/llm-meta-analysis/evaluation/data/annotated_rct_dataset.json
   description: Local scan hit; file_type=table_or_package; matched_query=effect_size sample_size original replication; path=data/raw/corpus_candidates/yun_llm_meta_analysis/llm-meta-analysis/evaluation/data/annotated_rct_dataset.csv; snippet=
   current heuristic reason: Matched Figure 1 code search query 'effect_size sample_size original replication'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=10; reasons=data_term:data | data_term:dataset | replication_word | original_word | local_table_or_code_surface | query_phrase_in_text

19. review_id: review_figure1_search_leads_9f4c421d1711
   lead_key: title:anonyize
   queue_status: needs_review
   name: anonyize
   record_kind: candidate_result_table
   inventory_status: needs_triage_search_lead
   url: data/raw/corpus_candidates/political_science_unlock/github/baraza/data/raw/anonyize.R
   source_key: data/raw/corpus_candidates/political_science_unlock/github/baraza/data/raw/anonyize.R
   description: Local scan hit; file_type=text_or_code; matched_query=direct_replication dataset; path=data/raw/corpus_candidates/political_science_unlock/github/baraza/data/raw/anonyize.R; snippet=
   current heuristic reason: Matched Figure 1 code search query 'direct_replication dataset'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=4; reasons=data_term:data | data_term:dataset | data_term:code | query_phrase_in_text

20. review_id: review_figure1_search_leads_f30f925a07d4
   lead_key: title:app
   queue_status: needs_review
   name: app
   record_kind: candidate_result_table
   inventory_status: needs_triage_search_lead
   url: data/raw/corpus_candidates/schimmack_bartos_y3gae/ShinyApp/app.R
   source_key: data/raw/corpus_candidates/schimmack_bartos_y3gae/ShinyApp/app.R
   description: Local scan hit; file_type=text_or_code; matched_query=paired replication table; path=data/raw/corpus_candidates/schimmack_bartos_y3gae/ShinyApp/app.R; snippet=
   current heuristic reason: Matched Figure 1 code search query 'paired replication table'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=8; reasons=data_term:data | data_term:code | replication_word | local_table_or_code_surface | query_phrase_in_text

```
