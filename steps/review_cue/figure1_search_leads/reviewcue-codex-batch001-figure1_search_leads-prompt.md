# figure1_search_leads Codex Review Prompt

Save returned JSON as `steps/review_cue/figure1_search_leads/reviewcue-decisions-figure1_search_leads-codex-batch001.json`.

```text
You are a Codex background reviewer for review cue `figure1_search_leads`.
Reusable bounded review queue for ambiguous Figure 1 corpus/database, repository-package, result-table, individual-paper, and context-source leads. Deterministic scripts should remove obvious duplicates and false positives first. Codex should investigate moderate batches and either make auditable decisions or emit compact GPT prompt requests for uncertain cases. GPT prompt batches can be larger because they are user-mediated review artifacts.

Work only this bounded batch. Investigate URLs and source metadata when useful.
Do not edit root tables. Return or save JSON decisions using the contract below.
Each accepted decision will later be applied as a per-lead receipt file, so future cue builds can skip it by checking for that target file.
If you are not confident, set decision to `needs_more_evidence` and include `user_gpt_prompt_request` with a compact prompt the user can give to GPT Pro.

Save decisions as: `steps/review_cue/figure1_search_leads/reviewcue-decisions-figure1_search_leads-codex-batch001.json`

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
1. review_id: review_figure1_search_leads_7207a6e0789b
   lead_key: title:additional_file_1_of_is_there_prejudice_from_thin_air_replicating_the_effect_of_emotion_on_automatic_intergroup_attitude
   queue_status: needs_root_candidate_review
   name: Additional file 1 of Is there prejudice from thin air? Replicating the effect of emotion on automatic intergroup attitudes
   record_kind: candidate_repository_package
   inventory_status: needs_triage_search_lead
   url: https://springernature.figshare.com/articles/journal_contribution/Additional_file_1_of_Is_there_prejudice_from_thin_air_Replicating_the_effect_of_emotion_on_automatic_intergroup_attitudes/12262283/1 | https://springernature.figshare.com/articles/journal_contribution/Additional_file_1_of_Is_there_prejudice_from_thin_air_Replicating_the_effect_of_emotion_on_automatic_intergroup_attitudes/12262283
   source_key: 10.6084/m9.figshare.12262283.v1 | 10.6084/m9.figshare.12262283
   description: Additional file 1.
   current heuristic reason: Matched Figure 1 link_graph search query '10.1126/science.aac4716'; lead_classification=publication_data_or_software_link_graph_hit; score=4; reasons=known_corpus_paper_link_graph

2. review_id: review_figure1_search_leads_da6e1c0421a5
   lead_key: title:additional_file_1_of_semantic_and_cognitive_tools_to_aid_statistical_science_replace_confidence_and_significance_by_comp
   queue_status: needs_root_candidate_review
   name: Additional file 1 of Semantic and cognitive tools to aid statistical science: replace confidence and significance by compatibility and surprise
   record_kind: candidate_repository_package
   inventory_status: needs_triage_search_lead
   url: https://springernature.figshare.com/articles/journal_contribution/Additional_file_1_of_Semantic_and_cognitive_tools_to_aid_statistical_science_replace_confidence_and_significance_by_compatibility_and_surprise/13031530 | https://springernature.figshare.com/articles/journal_contribution/Additional_file_1_of_Semantic_and_cognitive_tools_to_aid_statistical_science_replace_confidence_and_significance_by_compatibility_and_surprise/13031530/1
   source_key: 10.6084/m9.figshare.13031530 | 10.6084/m9.figshare.13031530.v1
   description: Additional file 1: Appendix. Technical details for computations of figures and tables.
   current heuristic reason: Matched Figure 1 link_graph search query '10.1126/science.aac4716'; lead_classification=publication_data_or_software_link_graph_hit; score=4; reasons=known_corpus_paper_link_graph

3. review_id: review_figure1_search_leads_6b43402f01f7
   lead_key: title:additional_file_1_of_the_reprise_project_protocol_for_an_evaluation_of_reproducibility_and_replicability_in_syntheses_of
   queue_status: needs_root_candidate_review
   name: Additional file 1 of The REPRISE project: protocol for an evaluation of REProducibility and Replicability In Syntheses of Evidence
   record_kind: candidate_repository_package
   inventory_status: needs_triage_search_lead
   url: https://springernature.figshare.com/articles/journal_contribution/Additional_file_1_of_The_REPRISE_project_protocol_for_an_evaluation_of_REProducibility_and_Replicability_In_Syntheses_of_Evidence/14442918/1 | https://springernature.figshare.com/articles/journal_contribution/Additional_file_1_of_The_REPRISE_project_protocol_for_an_evaluation_of_REProducibility_and_Replicability_In_Syntheses_of_Evidence/14442918
   source_key: 10.6084/m9.figshare.14442918.v1 | 10.6084/m9.figshare.14442918
   description: Additional file 1:. Search strategies
   current heuristic reason: Matched Figure 1 link_graph search query '10.7554/elife.04333'; lead_classification=publication_data_or_software_link_graph_hit; score=4; reasons=known_corpus_paper_link_graph

4. review_id: review_figure1_search_leads_714fabed70fe
   lead_key: title:additional_file_1_of_traditional_and_biomedical_care_pathways_for_mental_well_being_in_rural_nepal
   queue_status: needs_root_candidate_review
   name: Additional file 1 of Traditional and biomedical care pathways for mental well‐being in rural Nepal
   record_kind: candidate_repository_package
   inventory_status: needs_triage_search_lead
   url: https://springernature.figshare.com/articles/journal_contribution/Additional_file_1_of_Traditional_and_biomedical_care_pathways_for_mental_well_being_in_rural_Nepal/13545817/1 | https://springernature.figshare.com/articles/journal_contribution/Additional_file_1_of_Traditional_and_biomedical_care_pathways_for_mental_well_being_in_rural_Nepal/13545817
   source_key: 10.6084/m9.figshare.13545817.v1 | 10.6084/m9.figshare.13545817
   description: Additional file 1. Key illustrative quotes.
   current heuristic reason: Matched Figure 1 link_graph search query '10.1038/s41562-018-0399-z'; lead_classification=publication_data_or_software_link_graph_hit; score=4; reasons=known_corpus_paper_link_graph

5. review_id: review_figure1_search_leads_a0d3ac02fdf4
   lead_key: title:additional_file_2_of_traditional_and_biomedical_care_pathways_for_mental_well_being_in_rural_nepal
   queue_status: needs_root_candidate_review
   name: Additional file 2 of Traditional and biomedical care pathways for mental well‐being in rural Nepal
   record_kind: candidate_repository_package
   inventory_status: needs_triage_search_lead
   url: https://springernature.figshare.com/articles/journal_contribution/Additional_file_2_of_Traditional_and_biomedical_care_pathways_for_mental_well_being_in_rural_Nepal/13545820/1 | https://springernature.figshare.com/articles/journal_contribution/Additional_file_2_of_Traditional_and_biomedical_care_pathways_for_mental_well_being_in_rural_Nepal/13545820
   source_key: 10.6084/m9.figshare.13545820.v1 | 10.6084/m9.figshare.13545820
   description: Additional file 2. A research and policy framework for collaboration between healers and medical providers.
   current heuristic reason: Matched Figure 1 link_graph search query '10.1038/s41562-018-0399-z'; lead_classification=publication_data_or_software_link_graph_hit; score=4; reasons=known_corpus_paper_link_graph

6. review_id: review_figure1_search_leads_889e202a4dd5
   lead_key: title:ljcolling_fischerrrr_eyetracking_fischer_et_al_2003_multi_lab_replication_main_task
   queue_status: needs_root_candidate_review
   name: ljcolling/FischerRRR-eyetracking: Fischer et al (2003) multi-lab replication main task
   record_kind: candidate_repository_package
   inventory_status: needs_triage_search_lead
   url: https://zenodo.org/records/3406447
   source_key: 3406447
   description: <p>The PsychToolBox Code for the main task (eye-tracker version)</p>
   current heuristic reason: Matched Figure 1 repository search query '"multi-lab replication" "data"'; lead_classification=repository_hit_without_corpus_confirmation; score=4; reasons=data_term:code | replication_word | dataset_metadata_surface

7. review_id: review_figure1_search_leads_21b3e8caa4aa
   lead_key: title:pass_study_replication_dataset_msr25
   queue_status: needs_root_candidate_review
   name: pass-study-replication-dataset-msr25
   record_kind: candidate_repository_package
   inventory_status: needs_triage_search_lead
   url: https://zenodo.org/records/14066441
   source_key: 14066441
   description: <p>MSR25 technichal paper on Context-Driven LLM Summarization for Legacy&nbsp;Program Documentation</p>
   current heuristic reason: Matched Figure 1 repository search query '"replication dataset" "original study"'; lead_classification=repository_hit_without_corpus_confirmation; score=5; reasons=data_term:data | data_term:dataset | replication_word | dataset_metadata_surface

8. review_id: review_figure1_search_leads_f4f3c376d419
   lead_key: title:replication_package
   queue_status: needs_root_candidate_review
   name: Replication Package
   record_kind: candidate_repository_package
   inventory_status: needs_triage_search_lead
   url: https://doi.org/10.7910/DVN/KYJQPC
   source_key: doi:10.7910/DVN/KYJQPC
   description: We investigate the pass-through of a temporary value-added tax (VAT) cut on selected food products to consumer prices in Portugal. Exploiting a novel data set of daily online prices, we find that the VAT cut was fully transmitted to consumer prices, persisted throughout the policy duration, and prices returned to the pre-implementation trend after reversal. We discuss two potential mechanisms driving this result: the policy's salience to consumers in a high-inflation environment and the decline of producer prices when implemented. We estimate that the policy reduced the inflation rate by 0.68 percentage points on impact.
   current heuristic reason: Matched Figure 1 repository search query '"replication package" "original" "replication" "sample size"'; lead_classification=repository_hit_without_corpus_confirmation; score=4; reasons=data_term:data | replication_word | repository_data_surface

9. review_id: review_figure1_search_leads_38018a44fd54
   lead_key: title:rescience_c_contents
   queue_status: needs_root_candidate_review
   name: ReScience C contents
   record_kind: candidate_repository_package
   inventory_status: needs_triage_search_lead
   url: https://rescience.github.io/read/
   source_key: https://rescience.github.io/read/
   description: Static journal/source-family contents page for computational replication articles and code/review metadata. Page check: title=ReScience C; html_bytes=484221; link_count=1588
   current heuristic reason: Matched Figure 1 repository search query 'ReScience C replication contents code DOI review URL'; lead_classification=repository_hit_without_corpus_confirmation; score=4; reasons=data_term:data | data_term:code | replication_word

10. review_id: review_figure1_search_leads_1791596725b9
   lead_key: title:a_large_scale_in_silico_replication_of_ecological_and_evolutionary_studies
   queue_status: needs_root_candidate_review
   name: A large-scale in silico replication of ecological and evolutionary studies.
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1038/s41559-024-02530-5
   source_key: PMC11618063
   description: Despite the growing concerns about the replicability of ecological and evolutionary studies, no results exist from a field-wide replication project. We conduct a large-scale in silico replication project, leveraging cutting-edge statistical methodologies. Replicability is 30%-40% for studies with marginal statistical significance in the absence of selective reporting, whereas the replicability of studies presenting 'strong' evidence against the null hypothesis H<sub>0</sub> is >70%. The former requires a sevenfold larger sample size to reach the latter's replicability. We call for a change in planning, conducting and publishing research towards a transparent, credible and replicable ecology and evolution.
   current heuristic reason: Matched Figure 1 bibliographic search query '"replication project" "original study" "effect size"'; lead_classification=corpus_database_or_project_signal; score=15; reasons=strong_phrase:replication project | pair_term:sample size | pair_term:larger sample | replication_word | effect_or_sample_size_phrase | metadata_corpus_signal

11. review_id: review_figure1_search_leads_29d4d29c1ba2
   lead_key: title:a_large_scale_replication_of_scenario_based_experiments_in_psychology_and_management_using_large_language_models
   queue_status: needs_root_candidate_review
   name: A large-scale replication of scenario-based experiments in psychology and management using large language models
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1038/s43588-025-00840-7
   source_key: 10.1038/s43588-025-00840-7
   description: 
   current heuristic reason: Matched Figure 1 bibliographic search query '"large-scale replication" "dataset"'; lead_classification=corpus_database_or_project_signal; score=9; reasons=strong_phrase:large-scale replication | replication_word | metadata_corpus_signal

12. review_id: review_figure1_search_leads_ec299d9c57b4
   lead_key: title:a_multi_site_registered_replication_report_of_olson_amp_fazio_2001_implicit_attitude_formation_through_classical_conditi
   queue_status: needs_root_candidate_review
   name: A multi-site Registered Replication Report of Olson &amp; Fazio (2001) "Implicit Attitude Formation Through Classical Conditioning"
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://osf.io/3hjpf/
   source_key: 3hjpf
   description: NB nomenclature has changed over time: despite title of original article, "implicit" here refers to self-reported attitudes that were acquired in the absence of awareness/memory of the CS-US pairings (rather than classical conditioning procedures giving rise to implicit attitudes)
   current heuristic reason: Matched Figure 1 repository search query '"registered replication report" data'; lead_classification=corpus_database_or_project_signal; score=9; reasons=strong_phrase:registered replication report | replication_word | original_word

13. review_id: review_figure1_search_leads_6720e58edd1a
   lead_key: title:a_multilab_preregistered_replication_of_the_ego_depletion_effect
   queue_status: needs_root_candidate_review
   name: A Multilab Preregistered Replication of the Ego-Depletion Effect
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1177/1745691616652873
   source_key: https://openalex.org/W2499154041
   description: Good self-control has been linked to adaptive outcomes such as better health, cohesive personal relationships, success in the workplace and at school, and less susceptibility to crime and addictions. In contrast, self-control failure is linked to maladaptive outcomes. Understanding the mechanisms by which self-control predicts behavior may assist in promoting better regulation and outcomes. A popular approach to understanding self-control is the strength or resource depletion model. Self-control is conceptualized as a limited resource that becomes depleted after a period of exertion resulting in self-control failure. The model has typically been tested using a sequential-task experimental paradigm, in which people completing an initial self-control task have reduced self-control capacity and poorer performance on a subsequent task, a state known as ego depletion Although a meta-analysis of ego-depletion experiments found a medium-sized effect, subsequent meta-analyses have questioned the size and existence of the effect and identified instances of possible bias. The analyses served as a catalyst for the current Registered Replication Report of the ego-depletion effect. Multiple laboratories (k = 23, total N = 2,141) conducted replications of a standardized ego-depletion protocol based on a sequential-task paradigm by Sripada et al. Meta-analysis of the studies revealed that the size of the ego-depletion effect was small with 95% confidence intervals (CIs) that encompassed zero (d = 0.04, 95% CI [-0.07, 0.15]. We discuss implications of the findings for the ego-depletion eff
   current heuristic reason: Matched Figure 1 bibliographic search query '"registered replication report" "original study"'; lead_classification=corpus_database_or_project_signal; score=7; reasons=strong_phrase:registered replication report | replication_word

14. review_id: review_figure1_search_leads_434c463074a7
   lead_key: title:a_problem_in_theory_and_more_measuring_the_moderating_role_of_culture_in_many_labs_2
   queue_status: needs_root_candidate_review
   name: A Problem in Theory and More: Measuring the Moderating Role of Culture in Many Labs 2
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.31234/osf.io/hmnrx
   source_key: https://doi.org/10.31234/osf.io/hmnrx | https://openalex.org/W4319984852
   description: <p>The multi-site replication study, Many Labs 2 (ML2), attempted to test whether population, site and setting variability moderates the likelihood of replication and effect size. The analysis concluded that sample location and setting did not substantially affect the replicability of findings. In this paper, we raise several issues with the ML2 approach to adjudicating the effect of culture that cast doubt on this conclusion. These theoretical and methodological problems (pre-registered at https://osf.io/6exr4) involve the: (1) selection of studies and sample sites for replication that are not theory-driven, (2) sampling of mostly WEIRD people around the world, (3) conflation of participants’ cultural backgrounds with the country where the samples came from, (4) use of the WEIRD backronym by decomposing it into a scale, and (5) application of a mean split of that WEIRD variable. Moreover, simulations reveal strikingly low statistical power for detecting cultural influences in a multi-side study designed like ML2. We propose methodologies to address problems (3) to( 5) by re-analyzing the ML2 dataset using an alternative approach. These results suggest that tackling only some of the design problems is insufficient to overcome the underlying theoretical and methodological deficiencies. We conclude with specific recommendations for assessing the role of population variability in future multi-site studies that address evidentiary value and effect size.</p>
   current heuristic reason: Matched Figure 1 bibliographic search query '"multi-site replication" "dataset"'; lead_classification=corpus_database_or_project_signal; score=21; reasons=strong_phrase:many labs | strong_phrase:multi-site replication | pair_term:effect size | data_term:data | data_term:dataset | data_term:osf | replication_word | effect_or_sample_size_phrase | metadata_corpus_signal

15. review_id: review_figure1_search_leads_55a96c22e10c
   lead_key: title:a_scoping_review_on_metrics_to_quantify_reproducibility_a_multitude_of_questions_leads_to_a_multitude_of_metrics
   queue_status: needs_root_candidate_review
   name: A scoping review on metrics to quantify reproducibility: a multitude of questions leads to a multitude of metrics.
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1098/rsos.242076
   source_key: PMC12395386 | https://openalex.org/W4412464884
   description: Reproducibility is recognized as essential to scientific progress and integrity. Replication studies and large-scale replication projects, aiming to quantify different aspects of reproducibility, have become more common. Since no standardized approach to measuring reproducibility exists, a diverse set of metrics has emerged and a comprehensive overview is needed. We conducted a scoping review to identify large-scale replication projects that used metrics and methodological papers that proposed or discussed metrics. The project list was compiled by the authors. For the methodological papers, we searched Scopus, MedLine, PsycINFO and EconLit. Records were screened in duplicate against pre-defined inclusion criteria. Demographic information on included records and information on reproducibility metrics used, suggested or discussed was extracted. We identified 49 large-scale projects and 97 methodological papers and extracted 50 metrics. The metrics were characterized based on type (formulas and/or statistical models, frameworks, graphical representations, studies and questionnaires, algorithms), input required and appropriate application scenarios. Each metric addresses a distinct question. Our review provides a comprehensive resource in the form of a 'live', interactive table for future replication teams and meta-researchers, offering support in how to select the most appropriate metrics that are aligned with research questions and project goals.
   current heuristic reason: Matched Figure 1 bibliographic search query '"replication database" "original" "replication"'; lead_classification=corpus_database_or_project_signal; score=19; reasons=strong_phrase:replication project | strong_phrase:large-scale replication | strong_phrase:replication studies | replication_word | metadata_corpus_signal

16. review_id: review_figure1_search_leads_115f5ee33aea
   lead_key: title:absence_of_a_meaningful_effect_of_intranasal_oxytocin_on_trusting_behavior_a_registered_report_with_pooled_equivalence_t
   queue_status: needs_root_candidate_review
   name: Absence of a meaningful effect of intranasal oxytocin on trusting behavior: a registered report with pooled equivalence testing.
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1016/j.cortex.2026.03.006
   source_key: 41880977
   description: The neuropeptide oxytocin (OXT) is thought to modulate important aspects of prosocial behavior. In a seminal paper, Kosfeld et al. (2005) reported that intranasally administered OXT modulated trusting behavior in an economic trust game. Several attempts to conceptually replicate these findings yielded mixed results, which might be partly due to small sample sizes that can reduce the ability to detect, or reject, meaningful effects. We performed a large-scale replication (n = 211) of Kosfeld et al. (2005) with specific attention for small effects and subpopulations whose trusting behavior may be sensitive to OXT manipulations. Moreover, we conducted a pooled analysis of the two largest, recent, replications by merging our data with data from Declerck et al. (2020; n = 321). We found no evidence that intranasal OXT administration increases trusting behavior, neither in our data nor in the pooled dataset. While equivalence testing in our dataset was inconclusive, equivalence testing in the pooled dataset (n = 532) indicated that the effect of OXT administration on trusting behavior lies within a minimal range of effects, suggesting that the effect is too small to be of interest to (most) lab-based studies due to feasibility constraints of collecting data from larger samples required to reject smaller effect sizes. In addition, we found no evidence that OXT administration effects on trusting behavior are influenced by baseline trust, reward sensitivity, and punishment sensitivity. Our findings invite a critical evaluation of current methodology in OXT research and a reconsidera
   current heuristic reason: Matched Figure 1 bibliographic search query '"large-scale replication" "dataset"'; lead_classification=corpus_database_or_project_signal; score=18; reasons=strong_phrase:large-scale replication | pair_term:effect size | pair_term:sample size | pair_term:larger sample | data_term:data | data_term:dataset | data_term:osf | replication_word | metadata_corpus_signal

17. review_id: review_figure1_search_leads_b7d63ec6dc91
   lead_key: title:administering_a_victim_impact_curriculum_to_inmates_a_multi_site_replication
   queue_status: needs_root_candidate_review
   name: Administering a victim impact curriculum to inmates: a multi-site replication
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1080/1478601x.2015.1014037
   source_key: 10.1080/1478601x.2015.1014037
   description: 
   current heuristic reason: Matched Figure 1 domain search query '"multi-site" replication dataset original'; lead_classification=corpus_database_or_project_signal; score=9; reasons=strong_phrase:multi-site replication | replication_word | metadata_corpus_signal

18. review_id: review_figure1_search_leads_08428e8f58d8
   lead_key: title:advancing_the_cognitive_science_of_religion_through_replication_and_open_science
   queue_status: needs_root_candidate_review
   name: Advancing the Cognitive Science of Religion through Replication and Open Science
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1558/jcsr.39039
   source_key: https://openalex.org/W3096603764
   description: The Cognitive Science of Religion (CSR) is a relatively young but prolific field that has offered compelling insights into religious minds and practices. However, many empirical findings within this field are still preliminary and their reliability remains to be determined. In this paper, we first argue that it is crucial to critically evaluate the CSR literature and adopt open science practices and replication research in particular to move the field forward. Second, we highlight the outcomes of previous replications and make suggestions for future replication studies in the CSR, with a particular focus on neuroscience, developmental psychology, and qualitative research. Finally, we provide a “replication script” with advice on how to select, conduct, and organize replication research. Our approach is illustrated with a “glimpse behind the scenes” of the recently launched Cross-Cultural Religious Replication Project, in the hope of inspiring scholars of religion to embrace open science and replication in their own research.
   current heuristic reason: Matched Figure 1 citation search query '"Many Labs" "original study" -> cites:W3163230172'; lead_classification=corpus_database_or_project_signal; score=14; reasons=strong_phrase:replication project | strong_phrase:replication studies | replication_word | metadata_corpus_signal

19. review_id: review_figure1_search_leads_1a654f61e08b
   lead_key: title:an_open_investigation_of_the_reproducibility_of_cancer_biology_research
   queue_status: needs_root_candidate_review
   name: An open investigation of the reproducibility of cancer biology research
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.7554/elife.04333
   source_key: https://openalex.org/W2142148275
   description: It is widely believed that research that builds upon previously published findings has reproduced the original work. However, it is rare for researchers to perform or publish direct replications of existing results. The Reproducibility Project: Cancer Biology is an open investigation of reproducibility in preclinical cancer biology research. We have identified 50 high impact cancer biology articles published in the period 2010-2012, and plan to replicate a subset of experimental results from each article. A Registered Report detailing the proposed experimental designs and protocols for each subset of experiments will be peer reviewed and published prior to data collection. The results of these experiments will then be published in a Replication Study. The resulting open methodology and dataset will provide evidence about the reproducibility of high-impact results, and an opportunity to identify predictors of reproducibility.
   current heuristic reason: Matched Figure 1 citation search query '"SCORE" "scientific claims" "replication"'; lead_classification=corpus_database_or_project_signal; score=13; reasons=strong_phrase:reproducibility project | data_term:data | data_term:dataset | replication_word | original_word | metadata_corpus_signal

20. review_id: review_figure1_search_leads_d39d12c4d968
   lead_key: title:analysis_of_rare_parkinson_s_disease_variants_in_millions_of_people
   queue_status: needs_root_candidate_review
   name: Analysis of rare Parkinson’s disease variants in millions of people
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1038/s41531-023-00608-8
   source_key: https://openalex.org/W4390667162
   description: Although many rare variants have been reportedly associated with Parkinson's disease (PD), many have not been replicated or have failed to replicate. Here, we conduct a large-scale replication of rare PD variants. We assessed a total of 27,590 PD cases, 6701 PD proxies, and 3,106,080 controls from three data sets: 23andMe, Inc., UK Biobank, and AMP-PD. Based on well-known PD genes, 834 variants of interest were selected from the ClinVar annotated 23andMe dataset. We performed a meta-analysis using summary statistics of all three studies. The meta-analysis resulted in five significant variants after Bonferroni correction, including variants in GBA1 and LRRK2. Another eight variants are strong candidate variants for their association with PD. Here, we provide the largest rare variant meta-analysis to date, providing information on confirmed and newly identified variants for their association with PD using several large databases. Additionally we also show the complexities of studying rare variants in large-scale cohorts.
   current heuristic reason: Matched Figure 1 bibliographic search query '"large-scale replication" "dataset"'; lead_classification=corpus_database_or_project_signal; score=12; reasons=strong_phrase:large-scale replication | data_term:data | data_term:dataset | data_term:database | replication_word | metadata_corpus_signal

```
