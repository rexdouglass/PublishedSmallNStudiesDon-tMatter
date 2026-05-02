# figure1_search_leads Codex Review Prompt

Save returned JSON as `steps/review_cue/figure1_search_leads/reviewcue-decisions-figure1_search_leads-codex-reset001.json`.

```text
You are a Codex background reviewer for review cue `figure1_search_leads`.
Reusable bounded review queue for ambiguous Figure 1 corpus/database, repository-package, result-table, individual-paper, and context-source leads. Deterministic scripts should remove obvious duplicates and false positives first. Codex should investigate moderate batches and either make auditable decisions or emit compact GPT prompt requests for uncertain cases. GPT prompt batches can be larger because they are user-mediated review artifacts.

Work only this bounded batch. Investigate URLs and source metadata when useful.
Do not edit root tables. Return or save JSON decisions using the contract below.
Each accepted decision will later be applied as a per-lead receipt file, so future cue builds can skip it by checking for that target file.
If you are not confident, set decision to `needs_more_evidence` and include `user_gpt_prompt_request` with a compact prompt the user can give to GPT Pro.

Save decisions as: `steps/review_cue/figure1_search_leads/reviewcue-decisions-figure1_search_leads-codex-reset001.json`

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
1. review_id: review_figure1_search_leads_8deda84acf73
   lead_key: title:reproducibility_project_psychology_design
   queue_status: needs_root_candidate_review
   name: Reproducibility Project - Psychology: Design
   record_kind: candidate_corpus_or_database
   inventory_status: needs_triage_search_lead
   url: https://osf.io/i68pe/
   source_key: i68pe
   description: 
   current heuristic reason: Matched Figure 1 repository search query '"Reproducibility Project" coded data'; lead_classification=corpus_database_or_project_signal; score=5; reasons=strong_phrase:reproducibility project

2. review_id: review_figure1_search_leads_457c03b64b91
   lead_key: title:aea_rct_registry
   queue_status: needs_root_candidate_review
   name: AEA RCT Registry
   record_kind: candidate_repository_package
   inventory_status: needs_triage_search_lead
   url: reports/corpus_suggestion_tracker.md
   source_key: manual_tracker_row_aea_rct_registry_89598deb8a52
   description: Manual suggestion tracker row; status=worked as denominator scaffold; row=AEA RCT Registry | worked as denominator scaffold | Downloaded current registry CSV from `socialscienceregistry.org/site/csv`: 11,945 trials with status, primary outcomes, sample-size fields, PAP/data/program/relevant-paper fields. Dataverse snapshots are also accessible by API, but file download needs further API handling. | Best economics/social-science pre-publication denominator. | Registry has planned outcomes and sample sizes, but not publication-output coding or result effects. Need Leight/Asri/Imai output data or build searches/extraction.
   current heuristic reason: Matched Figure 1 manual search query 'papers or corpora mentioned in notes but not yet inventoried'; lead_classification=manual_artifact_without_corpus_confirmation; score=3; reasons=pair_term:sample size | data_term:data | data_term:dataverse | manual_tracker_status_signal | no_replication_language_penalty

3. review_id: review_figure1_search_leads_24a6bf58d703
   lead_key: title:barnett_wren_biomedical_ci_scrape_through_bear
   queue_status: needs_root_candidate_review
   name: Barnett/Wren biomedical CI scrape through BEAR
   record_kind: candidate_repository_package
   inventory_status: needs_triage_search_lead
   url: reports/corpus_suggestion_tracker.md
   source_key: manual_tracker_row_barnett_wren_biomedical_ci_scrape_through_bear_777c3caaf988
   description: Manual suggestion tracker row; status=partial; row=Barnett/Wren biomedical CI scrape through BEAR | partial | Used rough log-ratio-to-D conversion. | Huge published biomedical CI source; median `D ~= 0.357`, but no sample size and no treatment/main-outcome flag. | Background comparator only unless `N` can be recovered.
   current heuristic reason: Matched Figure 1 manual search query 'papers or corpora mentioned in notes but not yet inventoried'; lead_classification=manual_artifact_without_corpus_confirmation; score=3; reasons=pair_term:sample size | effect_or_sample_size_phrase | manual_tracker_status_signal | no_replication_language_penalty

4. review_id: review_figure1_search_leads_4420e14a8722
   lead_key: title:bear_combined_database
   queue_status: needs_root_candidate_review
   name: BEAR combined database
   record_kind: candidate_repository_package
   inventory_status: needs_triage_search_lead
   url: reports/corpus_suggestion_tracker.md
   source_key: manual_tracker_row_bear_combined_database_fcce1c1394c9
   description: Manual suggestion tracker row; status=working comparator; row=BEAR combined database | working comparator | Built `D_abs_best` where possible and audited every BEAR corpus for D, publication status, treatment-of-interest, and usable filters. | Many rows can get D, but most BEAR corpora are registry, review, replication, scrape, or meta-analysis objects. | Use as comparator/search index, not main backbone.
   current heuristic reason: Matched Figure 1 manual search query 'user-suggested replication datasets'; lead_classification=manual_artifact_without_corpus_confirmation; score=4; reasons=data_term:data | data_term:database | replication_word

5. review_id: review_figure1_search_leads_df7ca3924545
   lead_key: title:brodeur_economics_through_bear
   queue_status: needs_root_candidate_review
   name: Brodeur economics through BEAR
   record_kind: candidate_repository_package
   inventory_status: needs_triage_search_lead
   url: reports/corpus_suggestion_tracker.md
   source_key: manual_tracker_row_brodeur_economics_through_bear_865b5b0759ff
   description: Manual suggestion tracker row; status=rejected for BEAR version; row=Brodeur economics through BEAR | rejected for BEAR version | BEAR lacks sample size; our separate raw Brodeur 2024 file is better. | Use raw Dataverse instead.
   current heuristic reason: Matched Figure 1 manual search query 'papers or corpora mentioned in notes but not yet inventoried'; lead_classification=manual_artifact_without_corpus_confirmation; score=3; reasons=pair_term:sample size | data_term:data | data_term:dataverse | effect_or_sample_size_phrase | no_replication_language_penalty

6. review_id: review_figure1_search_leads_7fff8e566a13
   lead_key: title:combining_specific_task_oriented_training_with_manual_therapy_to_improve_balance_and_mobility_in_patients_after_stroke_a
   queue_status: needs_root_candidate_review
   name: Combining specific task-oriented training with manual therapy to improve balance and mobility in patients after stroke: a mixed methods pilot randomised controlled trial
   record_kind: candidate_repository_package
   inventory_status: needs_triage_search_lead
   url: https://tandf.figshare.com/articles/dataset/Combining_specific_task-oriented_training_with_manual_therapy_to_improve_balance_and_mobility_in_patients_after_stroke_a_mixed_methods_pilot_randomised_controlled_trial/22598456/1 | https://tandf.figshare.com/articles/dataset/Combining_specific_task-oriented_training_with_manual_therapy_to_improve_balance_and_mobility_in_patients_after_stroke_a_mixed_methods_pilot_randomised_controlled_trial/22598456
   source_key: 10.6084/m9.figshare.22598456.v1 | 10.6084/m9.figshare.22598456
   description: In absence of existing studies, to describe changes in balance and mobility, following specific task-oriented training (TOT), its combination with talocrural manual therapy (MT-TOT) or no intervention, in chronic stroke patients. To explore the feasibility of a full-scale randomised controlled trial (RCT) based on criteria of recruitment, retention and adherence rates, adverse events, falls and acceptability of the intervention. Using an assessor-blinded pilot RCT, 36 stroke patients were allocated to either MT-TOT, TOT, or controls. Supervised interventions were performed 45 min, 2×/weekly, for 4 weeks, and home-based practice 20 min, 4x/weekly for 4 weeks. Qualitative interviews evaluated intervention acceptability. Outcomes of balance, mobility, ankle dorsiflexion range of motion (ROM), falls and health-related quality of life (HRQoL) were assessed at baseline, post-intervention and 4-week follow-up. Preliminary efficacy of MT-TOT and TOT was shown in improving balance (effect size 0.714), walking speed (0.683), mobility (0.265), dual-tasking mobility (0.595), falls (0.037), active and passive talocrural ROM (0.603; 0.751) and activities and social participation related HRQoL domains (0.332–0.784) in stroke patients. The feasibility of a larger RCT was confirmed. Specific MT-TOT and TOT appeared effective and are feasible in stroke patients. A larger RCT is needed to validate the results.<b>Trial Registration:</b> German Clinical Trials Register, DRKS00023068. Registered on 21.09.2020, https://www.drks.de/drks_web/navigate.do?navigationId=trial.HTML&amp;TRIAL_ID=DRKS0002
   current heuristic reason: Matched Figure 1 repository search query '"pilot" "full-scale" trial effect size'; lead_classification=repository_hit_without_corpus_confirmation; score=5; reasons=pair_term:effect size | pair_term:full-scale | pair_term:pilot | effect_or_sample_size_phrase | no_replication_language_penalty

7. review_id: review_figure1_search_leads_e805304b48a0
   lead_key: title:direct_replications_in_the_era_of_open_sampling
   queue_status: needs_root_candidate_review
   name: Direct replications in the era of open sampling
   record_kind: candidate_repository_package
   inventory_status: needs_triage_search_lead
   url: https://osf.io/x2gfc/
   source_key: x2gfc
   description: Data collection in psychology increasingly relies on “open populations” of participants recruited online, which presents both opportunities and challenges for replication. Reduced costs and the possibility to access the same populations allows for more informative replications. However, researchers should ensure the directness of their replications by dealing with the threats of participant nonnaiveté and selection effects.
   current heuristic reason: Matched Figure 1 repository search query '"direct replication" data original replication'; lead_classification=repository_hit_without_corpus_confirmation; score=4; reasons=data_term:data | replication_word | repository_data_surface

8. review_id: review_figure1_search_leads_262bed40a6d0
   lead_key: title:headspace_for_parents_a_pilot_randomised_controlled_trial
   queue_status: needs_root_candidate_review
   name: Headspace for Parents: A Pilot Randomised Controlled Trial
   record_kind: candidate_repository_package
   inventory_status: needs_triage_search_lead
   url: https://osf.io/63av8/
   source_key: 63av8
   description: We will assess the effect sizes of an online, self-delivered mindfulness-based intervention (the Headspace app) for parents of children aged 2-5 years old on their children's externalising behaviour problems as measured by the Eyberg Child Behaviour Inventory. The study design is a three armed internal pilot randomised controlled trial, the initial sample size will be 35 per group, totalling 105 participants. Parents in the two intervention groups will be given access to the app for 40 days and asked to either use only the mindfulness content (group 1) or only the sleep aid content (group 2) on the app, parents in the wait list control group will get access to the app on completion of all three measures--the last set of which will occur at follow up, three months after the post-intervention measures.
   current heuristic reason: Matched Figure 1 repository search query '"pilot" "full-scale" trial effect size'; lead_classification=repository_hit_without_corpus_confirmation; score=5; reasons=pair_term:effect size | pair_term:sample size | pair_term:pilot | effect_or_sample_size_phrase | no_replication_language_penalty

9. review_id: review_figure1_search_leads_2e6894681b56
   lead_key: title:lancee_et_al_2017_antipsychotic_outcome_reporting_audit
   queue_status: needs_root_candidate_review
   name: Lancee et al. 2017 antipsychotic outcome-reporting audit
   record_kind: candidate_repository_package
   inventory_status: needs_triage_search_lead
   url: reports/corpus_suggestion_tracker.md
   source_key: manual_tracker_row_lancee_et_al_2017_antipsychotic_outcome_reporting_audit_558e313e20ef
   description: Manual suggestion tracker row; status=working comparator; row=Lancee et al. 2017 antipsychotic outcome-reporting audit | working comparator | Downloaded the Springer supplementary bundle. The `MOESM433` XLSX turned out to be a small wording crosswalk, while the useful public content is in `MOESM434`-`436` DOCX tables. | Real public registry-vs-publication discrepancy audit with study reference, NCT number, antipsychotic type, publication sample size, funding, region, and primary/secondary discrepancy flags. | Keep as a discrepancy-audit tracker, not a D/N source. The external memo overstated the XLSX as if it were the main tidy numeric dataset.
   current heuristic reason: Matched Figure 1 manual search query 'papers or corpora mentioned in notes but not yet inventoried'; lead_classification=manual_artifact_without_corpus_confirmation; score=4; reasons=pair_term:sample size | data_term:data | data_term:dataset | data_term:supplement | effect_or_sample_size_phrase | no_replication_language_penalty

10. review_id: review_figure1_search_leads_4dda2769be18
   lead_key: title:leight_asri_imai_aea_publication_tracking_paper
   queue_status: needs_root_candidate_review
   name: Leight/Asri/Imai AEA publication-tracking paper
   record_kind: candidate_repository_package
   inventory_status: needs_triage_search_lead
   url: reports/corpus_suggestion_tracker.md
   source_key: manual_tracker_row_leight_asri_imai_aea_publication_tracking_paper_c7e8b0f4ee3a
   description: Manual suggestion tracker row; status=paper downloaded; data not found; row=Leight/Asri/Imai AEA publication-tracking paper | paper downloaded; data not found | Downloaded working paper PDF. It describes 898 field trials from 2013-2016, 85% with public output, about 60% peer-reviewed, and abstract-coded primary-outcome/null reporting. | Conceptually excellent direct publication-bias study for economics. | I found the paper and preanalysis OSF link, but not a public row-level output dataset. Likely author-request or not yet posted.
   current heuristic reason: Matched Figure 1 manual search query 'papers or corpora mentioned in notes but not yet inventoried'; lead_classification=manual_artifact_without_corpus_confirmation; score=3; reasons=data_term:data | data_term:dataset | data_term:code | data_term:osf | manual_tracker_status_signal | no_replication_language_penalty

11. review_id: review_figure1_search_leads_6feeae3f5e15
   lead_key: title:nordic_trial_reporting_dataset
   queue_status: needs_root_candidate_review
   name: Nordic trial reporting dataset
   record_kind: candidate_repository_package
   inventory_status: needs_triage_search_lead
   url: reports/corpus_suggestion_tracker.md
   source_key: manual_tracker_row_nordic_trial_reporting_dataset_d5f6901cc693
   description: Manual suggestion tracker row; status=worked as scaffold; row=Nordic trial reporting dataset | worked as scaffold | Cloned `cathrineaxfors/nordic-trial-reporting`. Final publication file has 2,112 eligible trials with manually adjudicated `has_publication`, DOI, PMID, publication date/type; trial sample has enrollment, NCT/EUCTR, phase/status. | Excellent publication-status denominator and validation scaffold for AACT/EUCTR. | README explicitly says they did not assess whether publications reported the registered primary outcomes. No effect sizes. Needs AACT/registry and article extraction layer.
   current heuristic reason: Matched Figure 1 manual search query 'papers or corpora mentioned in notes but not yet inventoried'; lead_classification=manual_artifact_without_corpus_confirmation; score=3; reasons=pair_term:effect size | data_term:data | data_term:dataset | manual_tracker_status_signal | no_replication_language_penalty

12. review_id: review_figure1_search_leads_9fd64543e7b5
   lead_key: title:older_brodeur_methods_matter_openicpsr_file
   queue_status: needs_root_candidate_review
   name: Older Brodeur "Methods Matter" / OpenICPSR file
   record_kind: candidate_repository_package
   inventory_status: needs_triage_search_lead
   url: reports/corpus_suggestion_tracker.md
   source_key: manual_tracker_row_older_brodeur_methods_matter_openicpsr_file_be2c24ae9930
   description: Manual suggestion tracker row; status=worked as same recovered package; row=Older Brodeur "Methods Matter" / OpenICPSR file | worked as same recovered package | The older OpenICPSR target turned out to be the recovered 2016 Brodeur/Le/Sangnier/Zylberberg replication package. | Useful as a published-economics p/t comparator. | No further OpenICPSR chase needed here unless a separate sample-size-bearing file exists.
   current heuristic reason: Matched Figure 1 manual search query 'user-suggested replication datasets'; lead_classification=manual_artifact_without_corpus_confirmation; score=4; reasons=replication_word | manual_tracker_status_signal

13. review_id: review_figure1_search_leads_f04f5a33efba
   lead_key: title:replication_document_term_and_feature_matrices
   queue_status: needs_root_candidate_review
   name: Replication Document Term and Feature Matrices
   record_kind: candidate_repository_package
   inventory_status: needs_triage_search_lead
   url: https://doi.org/10.7910/DVN/KZW8R2
   source_key: doi:10.7910/DVN/KZW8R2
   description: Full replication data.
   current heuristic reason: Matched Figure 1 repository search query '"replication" "original_N" "replication_N"'; lead_classification=repository_hit_without_corpus_confirmation; score=4; reasons=data_term:data | replication_word | repository_data_surface

14. review_id: review_figure1_search_leads_2b41fd68366e
   lead_key: title:sips_2017_sample_size_and_effect_size_workshop
   queue_status: needs_root_candidate_review
   name: SIPS 2017 Sample Size and Effect Size Workshop
   record_kind: candidate_repository_package
   inventory_status: needs_triage_search_lead
   url: https://osf.io/ha4q8/
   source_key: ha4q8
   description: Workshop materials, slides, examples, and R code
   current heuristic reason: Matched Figure 1 repository search query '"replication project" effect size sample size'; lead_classification=repository_hit_without_corpus_confirmation; score=5; reasons=pair_term:effect size | pair_term:sample size | data_term:code | effect_or_sample_size_phrase | repository_data_surface | no_replication_language_penalty

15. review_id: review_figure1_search_leads_12b2fb987656
   lead_key: title:stanford_data
   queue_status: needs_root_candidate_review
   name: Stanford Data
   record_kind: candidate_repository_package
   inventory_status: needs_triage_search_lead
   url: https://doi.org/10.7910/DVN/CNTKLY
   source_key: doi:10.7910/DVN/CNTKLY
   description: Replication data from the Stanford analysis.
   current heuristic reason: Matched Figure 1 repository search query '"replication" "original_N" "replication_N"'; lead_classification=repository_hit_without_corpus_confirmation; score=4; reasons=data_term:data | replication_word | repository_data_surface

16. review_id: review_figure1_search_leads_6e23c48b1120
   lead_key: title:stroop_replication_study_dataset
   queue_status: needs_root_candidate_review
   name: Stroop Replication Study Dataset
   record_kind: candidate_repository_package
   inventory_status: needs_triage_search_lead
   url: https://osf.io/un4cb/
   source_key: un4cb
   description: Data was collected for an assignment for PSYCM0081 at the University of Bristol.
   current heuristic reason: Matched Figure 1 repository search query '"replication study" "original study" dataset'; lead_classification=repository_hit_without_corpus_confirmation; score=5; reasons=data_term:data | data_term:dataset | replication_word | repository_data_surface

17. review_id: review_figure1_search_leads_6f57ea519ab4
   lead_key: title:wp1_xp2a_book_of_n_white_replication_open_question
   queue_status: needs_root_candidate_review
   name: WP1 XP2a - Book of N: White [replication - open question]
   record_kind: candidate_repository_package
   inventory_status: needs_triage_search_lead
   url: https://osf.io/2qm8f/
   source_key: 2qm8f
   description: In a study (https://osf.io/xt458/?view_only=702e383b1228402fbab337f0b67f508c), we had Black and White (group membership, IV1) US participants read a scenario about a British professor using a potentially contentious original book title including the n-word rather than an alternative title not including the n-word. We investigated how participants’ preference for one book title over another (i.e., relative perception of norm; DV1) and the perception of blameworthiness of the Professor (i.e., blame; DV2) are influenced by people’s group membership (IV1) in interaction with their belief in systemic racial inequality (i.e., BSRI; IV2). In addition, we explored other variables, one of which was having participants respond to the open question: "How would you describe the situation and your thoughts about it to someone who wasn't there?" This preregistration concerns how we plan to analyze the responses to this exploratory open question.
   current heuristic reason: Matched Figure 1 repository search query '"original" "replication" "Cohen" "N"'; lead_classification=repository_hit_without_corpus_confirmation; score=5; reasons=data_term:osf | replication_word | original_word

18. review_id: review_figure1_search_leads_07969abf10b1
   lead_key: title:0_master
   queue_status: needs_review
   name: 0 Master
   record_kind: candidate_result_table
   inventory_status: needs_triage_search_lead
   url: data/raw/corpus_candidates/political_science_unlock/github/Direct-Aid-Replication-Materials/Replication Materials/Code/0_Master.do
   source_key: data/raw/corpus_candidates/political_science_unlock/github/Direct-Aid-Replication-Materials/Replication Materials/Code/0_Master.do
   description: Local scan hit; file_type=text_or_code; matched_query=paired replication table; path=data/raw/corpus_candidates/political_science_unlock/github/Direct-Aid-Replication-Materials/Replication Materials/Code/0_Master.do; snippet=
   current heuristic reason: Matched Figure 1 code search query 'paired replication table'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=8; reasons=data_term:data | data_term:code | replication_word | local_table_or_code_surface | query_phrase_in_text

19. review_id: review_figure1_search_leads_7019f9cdf939
   lead_key: title:2klnfx
   queue_status: needs_review
   name: 2KLNFX
   record_kind: candidate_result_table
   inventory_status: needs_triage_search_lead
   url: data/raw/corpus_candidates/political_science_unlock/dataverse_metadata/2KLNFX.json
   source_key: data/raw/corpus_candidates/political_science_unlock/dataverse_metadata/2KLNFX.json
   description: Local scan hit; file_type=table_or_package; matched_query=effect_size sample_size original replication; path=data/raw/corpus_candidates/political_science_unlock/dataverse_metadata/2KLNFX.json; snippet=
   current heuristic reason: Matched Figure 1 code search query 'effect_size sample_size original replication'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=10; reasons=data_term:data | data_term:dataverse | replication_word | original_word | local_table_or_code_surface | query_phrase_in_text

20. review_id: review_figure1_search_leads_7d811dec6207
   lead_key: title:3_replication_package_ufvur
   queue_status: needs_review
   name: 3-replication-package ufvur
   record_kind: candidate_result_table
   inventory_status: needs_triage_search_lead
   url: data/raw/corpus_candidates/political_science_unlock/zenodo/10059860/3-replication-package_ufvur.zip
   source_key: data/raw/corpus_candidates/political_science_unlock/zenodo/10059860/3-replication-package_ufvur.zip
   description: Local scan hit; file_type=table_or_package; matched_query=effect_size sample_size original replication; path=data/raw/corpus_candidates/political_science_unlock/zenodo/10059860/3-replication-package_ufvur.zip; snippet=
   current heuristic reason: Matched Figure 1 code search query 'effect_size sample_size original replication'; lead_classification=local_file_or_header_hit_without_corpus_confirmation; score=9; reasons=data_term:data | replication_word | original_word | local_table_or_code_surface | query_phrase_in_text

```
