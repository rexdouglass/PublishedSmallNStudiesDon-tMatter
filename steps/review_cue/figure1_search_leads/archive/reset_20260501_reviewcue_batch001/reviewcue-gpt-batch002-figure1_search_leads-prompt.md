# figure1_search_leads Gpt Review Prompt

Save returned JSON as `steps/review_cue/figure1_search_leads/reviewcue-decisions-figure1_search_leads-gpt-batch002.json`.

```text
You are reviewing `figure1_search_leads` leads for a provenance pipeline.
Use web research if needed. Do not infer relevance from search terms alone.
Classify up to 50 leads. Be conservative: reject or route away if the source is only an individual paper, method paper, or irrelevant false positive.
Each decision will later become a per-lead receipt file, so future cue builds can skip reviewed items by target-file existence.

The user will save your JSON as: `steps/review_cue/figure1_search_leads/reviewcue-decisions-figure1_search_leads-gpt-batch002.json`

Allowed decisions:
- keep_in_corpora_and_databases
- promote_to_corpora_and_databases
- route_to_result_table_worklist
- route_to_individual_replication_paper_worklist
- keep_as_context_source
- reject_irrelevant
- needs_more_evidence

Return JSON only, with a `decisions` array. Required fields:
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

For `needs_more_evidence`, say exactly what source, page, file, or identifier should be checked next.

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

21. review_id: review_figure1_search_leads_1d897532f337
   lead_key: title:armington
   queue_status: needs_review
   name: armington
   record_kind: candidate_result_table
   inventory_status: needs_triage_search_lead
   url: data/raw/corpus_candidates/havranek_meta_analysis/armington/armington.do
   source_key: data/raw/corpus_candidates/havranek_meta_analysis/armington/armington.do
   description: Local scan hit; file_type=text_or_code; matched_query=paired replication table; path=data/raw/corpus_candidates/havranek_meta_analysis/armington/armington.do; snippet=
   current heuristic reason: Matched Figure 1 code search query 'paired replication table'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=8; reasons=data_term:data | data_term:code | replication_word | local_table_or_code_surface | query_phrase_in_text

22. review_id: review_figure1_search_leads_d337e2f27cdf
   lead_key: title:article
   queue_status: needs_review
   name: article
   record_kind: candidate_result_table
   inventory_status: needs_triage_search_lead
   url: data/raw/corpus_candidates/linden_2024/article.html | data/raw/corpus_candidates/kuhberger_2014/article.html
   source_key: data/raw/corpus_candidates/linden_2024/article.html | data/raw/corpus_candidates/kuhberger_2014/article.html
   description: Local scan hit; file_type=text_or_code; matched_query=paired replication table; path=data/raw/corpus_candidates/linden_2024/article.html; snippet=lication_date=2019;"/> <meta name="citation_reference" content="citation_title=Publication bias in psychology: a diagnosis based on the correlation between effect size and sample size;citation_author=A. Kühberger;citation_author=A. Fritz;citation_author=T. Scherndl;citation_volume=9;citation_number=9;citation_issue=9;citation_first_page=e105
   current heuristic reason: Matched Figure 1 code search query 'paired replication table'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=14; reasons=pair_term:effect size | pair_term:sample size | data_term:data | data_term:code | replication_word | effect_or_sample_size_phrase | local_table_or_code_surface | query_phrase_in_text

23. review_id: review_figure1_search_leads_60a5f3c4538b
   lead_key: title:article_24225157
   queue_status: needs_review
   name: article 24225157
   record_kind: candidate_result_table
   inventory_status: needs_triage_search_lead
   url: data/raw/corpus_candidates/ctgov_kg/article_24225157.json
   source_key: data/raw/corpus_candidates/ctgov_kg/article_24225157.json
   description: Local scan hit; file_type=table_or_package; matched_query=direct_replication dataset; path=data/raw/corpus_candidates/ctgov_kg/article_24225157.json; snippet=
   current heuristic reason: Matched Figure 1 code search query 'direct_replication dataset'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=6; reasons=data_term:data | data_term:dataset | local_table_or_code_surface | query_phrase_in_text

24. review_id: review_figure1_search_leads_a5e0515a7942
   lead_key: title:article_24225160
   queue_status: needs_review
   name: article 24225160
   record_kind: candidate_result_table
   inventory_status: needs_triage_search_lead
   url: data/raw/corpus_candidates/ctgov_kg/article_24225160.json
   source_key: data/raw/corpus_candidates/ctgov_kg/article_24225160.json
   description: Local scan hit; file_type=table_or_package; matched_query=direct_replication dataset; path=data/raw/corpus_candidates/ctgov_kg/article_24225160.json; snippet=
   current heuristic reason: Matched Figure 1 code search query 'direct_replication dataset'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=6; reasons=data_term:data | data_term:dataset | local_table_or_code_surface | query_phrase_in_text

25. review_id: review_figure1_search_leads_08e3fd3d5d51
   lead_key: title:article_24225163
   queue_status: needs_review
   name: article 24225163
   record_kind: candidate_result_table
   inventory_status: needs_triage_search_lead
   url: data/raw/corpus_candidates/ctgov_kg/article_24225163.json
   source_key: data/raw/corpus_candidates/ctgov_kg/article_24225163.json
   description: Local scan hit; file_type=table_or_package; matched_query=direct_replication dataset; path=data/raw/corpus_candidates/ctgov_kg/article_24225163.json; snippet=
   current heuristic reason: Matched Figure 1 code search query 'direct_replication dataset'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=6; reasons=data_term:data | data_term:dataset | local_table_or_code_surface | query_phrase_in_text

26. review_id: review_figure1_search_leads_8c7268945daf
   lead_key: title:article_24225166
   queue_status: needs_review
   name: article 24225166
   record_kind: candidate_result_table
   inventory_status: needs_triage_search_lead
   url: data/raw/corpus_candidates/ctgov_kg/article_24225166.json
   source_key: data/raw/corpus_candidates/ctgov_kg/article_24225166.json
   description: Local scan hit; file_type=table_or_package; matched_query=direct_replication dataset; path=data/raw/corpus_candidates/ctgov_kg/article_24225166.json; snippet=
   current heuristic reason: Matched Figure 1 code search query 'direct_replication dataset'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=6; reasons=data_term:data | data_term:dataset | local_table_or_code_surface | query_phrase_in_text

27. review_id: review_figure1_search_leads_e37672d60d04
   lead_key: title:article_24225169
   queue_status: needs_review
   name: article 24225169
   record_kind: candidate_result_table
   inventory_status: needs_triage_search_lead
   url: data/raw/corpus_candidates/ctgov_kg/article_24225169.json
   source_key: data/raw/corpus_candidates/ctgov_kg/article_24225169.json
   description: Local scan hit; file_type=table_or_package; matched_query=direct_replication dataset; path=data/raw/corpus_candidates/ctgov_kg/article_24225169.json; snippet=
   current heuristic reason: Matched Figure 1 code search query 'direct_replication dataset'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=6; reasons=data_term:data | data_term:dataset | local_table_or_code_surface | query_phrase_in_text

28. review_id: review_figure1_search_leads_233911291f62
   lead_key: title:article_24225172
   queue_status: needs_review
   name: article 24225172
   record_kind: candidate_result_table
   inventory_status: needs_triage_search_lead
   url: data/raw/corpus_candidates/ctgov_kg/article_24225172.json
   source_key: data/raw/corpus_candidates/ctgov_kg/article_24225172.json
   description: Local scan hit; file_type=table_or_package; matched_query=direct_replication dataset; path=data/raw/corpus_candidates/ctgov_kg/article_24225172.json; snippet=
   current heuristic reason: Matched Figure 1 code search query 'direct_replication dataset'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=6; reasons=data_term:data | data_term:dataset | local_table_or_code_surface | query_phrase_in_text

29. review_id: review_figure1_search_leads_036a245f5e42
   lead_key: title:article_24630804
   queue_status: needs_review
   name: article 24630804
   record_kind: candidate_result_table
   inventory_status: needs_triage_search_lead
   url: data/raw/corpus_candidates/ctgov_kg/article_24630804.json
   source_key: data/raw/corpus_candidates/ctgov_kg/article_24630804.json
   description: Local scan hit; file_type=table_or_package; matched_query=direct_replication dataset; path=data/raw/corpus_candidates/ctgov_kg/article_24630804.json; snippet=
   current heuristic reason: Matched Figure 1 code search query 'direct_replication dataset'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=6; reasons=data_term:data | data_term:dataset | local_table_or_code_surface | query_phrase_in_text

30. review_id: review_figure1_search_leads_997cb4c71ec0
   lead_key: title:article_24633666
   queue_status: needs_review
   name: article 24633666
   record_kind: candidate_result_table
   inventory_status: needs_triage_search_lead
   url: data/raw/corpus_candidates/ctgov_kg/article_24633666.json
   source_key: data/raw/corpus_candidates/ctgov_kg/article_24633666.json
   description: Local scan hit; file_type=table_or_package; matched_query=direct_replication dataset; path=data/raw/corpus_candidates/ctgov_kg/article_24633666.json; snippet=
   current heuristic reason: Matched Figure 1 code search query 'direct_replication dataset'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=6; reasons=data_term:data | data_term:dataset | local_table_or_code_surface | query_phrase_in_text

31. review_id: review_figure1_search_leads_d1467a6ac5d9
   lead_key: title:article_24633669
   queue_status: needs_review
   name: article 24633669
   record_kind: candidate_result_table
   inventory_status: needs_triage_search_lead
   url: data/raw/corpus_candidates/ctgov_kg/article_24633669.json
   source_key: data/raw/corpus_candidates/ctgov_kg/article_24633669.json
   description: Local scan hit; file_type=table_or_package; matched_query=direct_replication dataset; path=data/raw/corpus_candidates/ctgov_kg/article_24633669.json; snippet=
   current heuristic reason: Matched Figure 1 code search query 'direct_replication dataset'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=6; reasons=data_term:data | data_term:dataset | local_table_or_code_surface | query_phrase_in_text

32. review_id: review_figure1_search_leads_3831d939bb32
   lead_key: title:article_24633672
   queue_status: needs_review
   name: article 24633672
   record_kind: candidate_result_table
   inventory_status: needs_triage_search_lead
   url: data/raw/corpus_candidates/ctgov_kg/article_24633672.json
   source_key: data/raw/corpus_candidates/ctgov_kg/article_24633672.json
   description: Local scan hit; file_type=table_or_package; matched_query=direct_replication dataset; path=data/raw/corpus_candidates/ctgov_kg/article_24633672.json; snippet=
   current heuristic reason: Matched Figure 1 code search query 'direct_replication dataset'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=6; reasons=data_term:data | data_term:dataset | local_table_or_code_surface | query_phrase_in_text

33. review_id: review_figure1_search_leads_388841946ed6
   lead_key: title:article_24633675
   queue_status: needs_review
   name: article 24633675
   record_kind: candidate_result_table
   inventory_status: needs_triage_search_lead
   url: data/raw/corpus_candidates/ctgov_kg/article_24633675.json
   source_key: data/raw/corpus_candidates/ctgov_kg/article_24633675.json
   description: Local scan hit; file_type=table_or_package; matched_query=direct_replication dataset; path=data/raw/corpus_candidates/ctgov_kg/article_24633675.json; snippet=
   current heuristic reason: Matched Figure 1 code search query 'direct_replication dataset'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=6; reasons=data_term:data | data_term:dataset | local_table_or_code_surface | query_phrase_in_text

34. review_id: review_figure1_search_leads_65ed1a4faa08
   lead_key: title:article_reader
   queue_status: needs_review
   name: article reader
   record_kind: candidate_result_table
   inventory_status: needs_triage_search_lead
   url: data/raw/corpus_candidates/evidence_inference/evidence-inference/evidence_inference/preprocess/article_reader.py
   source_key: data/raw/corpus_candidates/evidence_inference/evidence-inference/evidence_inference/preprocess/article_reader.py
   description: Local scan hit; file_type=text_or_code; matched_query=paired replication table; path=data/raw/corpus_candidates/evidence_inference/evidence-inference/evidence_inference/preprocess/article_reader.py; snippet=
   current heuristic reason: Matched Figure 1 code search query 'paired replication table'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=8; reasons=data_term:data | data_term:code | replication_word | local_table_or_code_surface | query_phrase_in_text

35. review_id: review_figure1_search_leads_a0897b96bcfb
   lead_key: title:attrition
   queue_status: needs_review
   name: attrition
   record_kind: candidate_result_table
   inventory_status: needs_triage_search_lead
   url: data/raw/corpus_candidates/political_science_unlock/github/baraza/report/attrition.R
   source_key: data/raw/corpus_candidates/political_science_unlock/github/baraza/report/attrition.R
   description: Local scan hit; file_type=text_or_code; matched_query=direct_replication dataset; path=data/raw/corpus_candidates/political_science_unlock/github/baraza/report/attrition.R; snippet=
   current heuristic reason: Matched Figure 1 code search query 'direct_replication dataset'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=4; reasons=data_term:data | data_term:dataset | data_term:code | query_phrase_in_text

36. review_id: review_figure1_search_leads_f9fbabeb7093
   lead_key: title:b1_filter_intervention_comparator
   queue_status: needs_review
   name: b1 filter intervention comparator
   record_kind: candidate_result_table
   inventory_status: needs_triage_search_lead
   url: data/raw/corpus_candidates/clinifact/CliniFact/scripts/b1_filter_intervention_comparator.py
   source_key: data/raw/corpus_candidates/clinifact/CliniFact/scripts/b1_filter_intervention_comparator.py
   description: Local scan hit; file_type=text_or_code; matched_query=effect_size sample_size original replication; path=data/raw/corpus_candidates/clinifact/CliniFact/scripts/b1_filter_intervention_comparator.py; snippet=
   current heuristic reason: Matched Figure 1 code search query 'effect_size sample_size original replication'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=7; reasons=data_term:data | data_term:code | replication_word | original_word | query_phrase_in_text

37. review_id: review_figure1_search_leads_c164ed296299
   lead_key: title:balance
   queue_status: needs_review
   name: balance
   record_kind: candidate_result_table
   inventory_status: needs_triage_search_lead
   url: data/raw/corpus_candidates/political_science_unlock/github/baraza/sc_report/balance.R
   source_key: data/raw/corpus_candidates/political_science_unlock/github/baraza/sc_report/balance.R
   description: Local scan hit; file_type=text_or_code; matched_query=paired replication table; path=data/raw/corpus_candidates/political_science_unlock/github/baraza/sc_report/balance.R; snippet=
   current heuristic reason: Matched Figure 1 code search query 'paired replication table'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=8; reasons=data_term:data | data_term:code | replication_word | local_table_or_code_surface | query_phrase_in_text

38. review_id: review_figure1_search_leads_2937084614d6
   lead_key: title:c_extract_stance_label
   queue_status: needs_review
   name: c extract stance label
   record_kind: candidate_result_table
   inventory_status: needs_triage_search_lead
   url: data/raw/corpus_candidates/clinifact/CliniFact/scripts/c_extract_stance_label.py
   source_key: data/raw/corpus_candidates/clinifact/CliniFact/scripts/c_extract_stance_label.py
   description: Local scan hit; file_type=text_or_code; matched_query=effect_size sample_size original replication; path=data/raw/corpus_candidates/clinifact/CliniFact/scripts/c_extract_stance_label.py; snippet=
   current heuristic reason: Matched Figure 1 code search query 'effect_size sample_size original replication'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=7; reasons=data_term:data | data_term:code | replication_word | original_word | query_phrase_in_text

39. review_id: review_figure1_search_leads_24d02540a0b8
   lead_key: title:calculate_metrics
   queue_status: needs_review
   name: calculate metrics
   record_kind: candidate_result_table
   inventory_status: needs_triage_search_lead
   url: data/raw/corpus_candidates/yun_llm_meta_analysis/llm-meta-analysis/evaluation/calculate_metrics.py
   source_key: data/raw/corpus_candidates/yun_llm_meta_analysis/llm-meta-analysis/evaluation/calculate_metrics.py
   description: Local scan hit; file_type=text_or_code; matched_query=paired replication table; path=data/raw/corpus_candidates/yun_llm_meta_analysis/llm-meta-analysis/evaluation/calculate_metrics.py; snippet=
   current heuristic reason: Matched Figure 1 code search query 'paired replication table'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=8; reasons=data_term:data | data_term:code | replication_word | local_table_or_code_surface | query_phrase_in_text

40. review_id: review_figure1_search_leads_6edefa492739
   lead_key: title:cleanedbaselinedata
   queue_status: needs_review
   name: cleanedBaselineData
   record_kind: candidate_result_table
   inventory_status: needs_triage_search_lead
   url: data/raw/corpus_candidates/political_science_unlock/github/Direct-Aid-Replication-Materials/Replication Materials/Data/cleanedBaselineData.dta
   source_key: data/raw/corpus_candidates/political_science_unlock/github/Direct-Aid-Replication-Materials/Replication Materials/Data/cleanedBaselineData.dta
   description: Local scan hit; file_type=table_or_package; matched_query=effect_size sample_size original replication; path=data/raw/corpus_candidates/political_science_unlock/github/Direct-Aid-Replication-Materials/Replication Materials/Data/cleanedBaselineData.dta; snippet=
   current heuristic reason: Matched Figure 1 code search query 'effect_size sample_size original replication'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=9; reasons=data_term:data | replication_word | original_word | local_table_or_code_surface | query_phrase_in_text

41. review_id: review_figure1_search_leads_88f4051eba55
   lead_key: title:cleanedfollowupdata
   queue_status: needs_review
   name: cleanedFollowUpData
   record_kind: candidate_result_table
   inventory_status: needs_triage_search_lead
   url: data/raw/corpus_candidates/political_science_unlock/github/Direct-Aid-Replication-Materials/Replication Materials/Data/cleanedFollowUpData.dta
   source_key: data/raw/corpus_candidates/political_science_unlock/github/Direct-Aid-Replication-Materials/Replication Materials/Data/cleanedFollowUpData.dta
   description: Local scan hit; file_type=table_or_package; matched_query=effect_size sample_size original replication; path=data/raw/corpus_candidates/political_science_unlock/github/Direct-Aid-Replication-Materials/Replication Materials/Data/cleanedFollowUpData.dta; snippet=
   current heuristic reason: Matched Figure 1 code search query 'effect_size sample_size original replication'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=9; reasons=data_term:data | replication_word | original_word | local_table_or_code_surface | query_phrase_in_text

42. review_id: review_figure1_search_leads_bcb56744ee19
   lead_key: title:cleanedtransactiondata
   queue_status: needs_review
   name: cleanedTransactionData
   record_kind: candidate_result_table
   inventory_status: needs_triage_search_lead
   url: data/raw/corpus_candidates/political_science_unlock/github/Direct-Aid-Replication-Materials/Replication Materials/Data/cleanedTransactionData.dta
   source_key: data/raw/corpus_candidates/political_science_unlock/github/Direct-Aid-Replication-Materials/Replication Materials/Data/cleanedTransactionData.dta
   description: Local scan hit; file_type=table_or_package; matched_query=effect_size sample_size original replication; path=data/raw/corpus_candidates/political_science_unlock/github/Direct-Aid-Replication-Materials/Replication Materials/Data/cleanedTransactionData.dta; snippet=
   current heuristic reason: Matched Figure 1 code search query 'effect_size sample_size original replication'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=9; reasons=data_term:data | replication_word | original_word | local_table_or_code_surface | query_phrase_in_text

43. review_id: review_figure1_search_leads_c3b22dac2ae2
   lead_key: title:compare_recoding
   queue_status: needs_review
   name: compare recoding
   record_kind: candidate_result_table
   inventory_status: needs_triage_search_lead
   url: data/raw/corpus_candidates/schimmack_bartos_y3gae/re-analysis/compare_recoding.R
   source_key: data/raw/corpus_candidates/schimmack_bartos_y3gae/re-analysis/compare_recoding.R
   description: Local scan hit; file_type=text_or_code; matched_query=paired replication table; path=data/raw/corpus_candidates/schimmack_bartos_y3gae/re-analysis/compare_recoding.R; snippet=
   current heuristic reason: Matched Figure 1 code search query 'paired replication table'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=8; reasons=data_term:data | data_term:code | replication_word | local_table_or_code_surface | query_phrase_in_text

44. review_id: review_figure1_search_leads_07c47d4073ef
   lead_key: title:comparison_group_analysis
   queue_status: needs_review
   name: comparison-group-analysis
   record_kind: candidate_result_table
   inventory_status: needs_triage_search_lead
   url: data/raw/corpus_candidates/political_science_unlock/zenodo/3942437/comparison-group-analysis.R
   source_key: data/raw/corpus_candidates/political_science_unlock/zenodo/3942437/comparison-group-analysis.R
   description: Local scan hit; file_type=text_or_code; matched_query=effect_size sample_size original replication; path=data/raw/corpus_candidates/political_science_unlock/zenodo/3942437/comparison-group-analysis.R; snippet=
   current heuristic reason: Matched Figure 1 code search query 'effect_size sample_size original replication'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=7; reasons=data_term:data | data_term:code | replication_word | original_word | query_phrase_in_text

45. review_id: review_figure1_search_leads_b1137d0babae
   lead_key: title:compute_effect_size
   queue_status: needs_review
   name: compute effect size
   record_kind: candidate_result_table
   inventory_status: needs_triage_search_lead
   url: data/raw/corpus_candidates/metalab/metalabr/R/compute_effect_size.R
   source_key: data/raw/corpus_candidates/metalab/metalabr/R/compute_effect_size.R
   description: Local scan hit; file_type=text_or_code; matched_query=effect_size sample_size original replication; path=data/raw/corpus_candidates/metalab/metalabr/R/compute_effect_size.R; snippet=
   current heuristic reason: Matched Figure 1 code search query 'effect_size sample_size original replication'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=11; reasons=pair_term:effect size | data_term:data | data_term:code | replication_word | original_word | effect_or_sample_size_phrase | query_phrase_in_text

46. review_id: review_figure1_search_leads_54e195f7a9af
   lead_key: title:correlational_effect_size_benchmarks
   queue_status: needs_review
   name: correlational effect size benchmarks
   record_kind: candidate_result_table
   inventory_status: needs_triage_search_lead
   url: data/raw/corpus_candidates/metabus/correlational_effect_size_benchmarks.html
   source_key: data/raw/corpus_candidates/metabus/correlational_effect_size_benchmarks.html
   description: Local scan hit; file_type=text_or_code; matched_query=effect_size sample_size original replication; path=data/raw/corpus_candidates/metabus/correlational_effect_size_benchmarks.html; snippet=
   current heuristic reason: Matched Figure 1 code search query 'effect_size sample_size original replication'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=11; reasons=pair_term:effect size | data_term:data | data_term:code | replication_word | original_word | effect_or_sample_size_phrase | query_phrase_in_text

47. review_id: review_figure1_search_leads_d737f3e43bbc
   lead_key: title:costeffcalculations
   queue_status: needs_review
   name: CostEffCalculations
   record_kind: candidate_result_table
   inventory_status: needs_triage_search_lead
   url: data/raw/corpus_candidates/political_science_unlock/github/Direct-Aid-Replication-Materials/Replication Materials/Code/CostEffCalculations.xlsx
   source_key: data/raw/corpus_candidates/political_science_unlock/github/Direct-Aid-Replication-Materials/Replication Materials/Code/CostEffCalculations.xlsx
   description: Local scan hit; file_type=table_or_package; matched_query=effect_size sample_size original replication; path=data/raw/corpus_candidates/political_science_unlock/github/Direct-Aid-Replication-Materials/Replication Materials/Code/CostEffCalculations.xlsx; snippet=
   current heuristic reason: Matched Figure 1 code search query 'effect_size sample_size original replication'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=10; reasons=data_term:data | data_term:code | replication_word | original_word | local_table_or_code_surface | query_phrase_in_text

48. review_id: review_figure1_search_leads_c061e931f671
   lead_key: title:counterfactuals
   queue_status: needs_review
   name: counterfactuals
   record_kind: candidate_result_table
   inventory_status: needs_triage_search_lead
   url: data/raw/corpus_candidates/dellavigna_linos/unzipped/counterfactuals.m
   source_key: data/raw/corpus_candidates/dellavigna_linos/unzipped/counterfactuals.m
   description: Local scan hit; file_type=text_or_code; matched_query=paired replication table; path=data/raw/corpus_candidates/dellavigna_linos/unzipped/counterfactuals.m; snippet=
   current heuristic reason: Matched Figure 1 code search query 'paired replication table'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=8; reasons=data_term:data | data_term:code | replication_word | local_table_or_code_surface | query_phrase_in_text

49. review_id: review_figure1_search_leads_1aafc15d61c5
   lead_key: title:dataset
   queue_status: needs_review
   name: DATASET
   record_kind: candidate_result_table
   inventory_status: needs_triage_search_lead
   url: data/raw/corpus_candidates/yun_llm_meta_analysis/llm-meta-analysis/evaluation/data/DATASET.md
   source_key: data/raw/corpus_candidates/yun_llm_meta_analysis/llm-meta-analysis/evaluation/data/DATASET.md
   description: Local scan hit; file_type=text_or_code; matched_query=direct_replication dataset; path=data/raw/corpus_candidates/yun_llm_meta_analysis/llm-meta-analysis/evaluation/data/DATASET.md; snippet=
   current heuristic reason: Matched Figure 1 code search query 'direct_replication dataset'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=4; reasons=data_term:data | data_term:dataset | data_term:code | query_phrase_in_text

50. review_id: review_figure1_search_leads_00d54a89bac3
   lead_key: title:densities
   queue_status: needs_review
   name: densities
   record_kind: candidate_result_table
   inventory_status: needs_triage_search_lead
   url: data/raw/corpus_candidates/dellavigna_linos/unzipped/densities.m
   source_key: data/raw/corpus_candidates/dellavigna_linos/unzipped/densities.m
   description: Local scan hit; file_type=text_or_code; matched_query=paired replication table; path=data/raw/corpus_candidates/dellavigna_linos/unzipped/densities.m; snippet=
   current heuristic reason: Matched Figure 1 code search query 'paired replication table'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=8; reasons=data_term:data | data_term:code | replication_word | local_table_or_code_surface | query_phrase_in_text

```
