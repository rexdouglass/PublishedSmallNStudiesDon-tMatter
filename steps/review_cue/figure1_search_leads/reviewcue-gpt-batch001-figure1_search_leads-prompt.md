# figure1_search_leads Gpt Review Prompt

Save returned JSON as `steps/review_cue/figure1_search_leads/reviewcue-decisions-figure1_search_leads-gpt-batch001.json`.

```text
You are reviewing `figure1_search_leads` leads for a provenance pipeline.
Use web research if needed. Do not infer relevance from search terms alone.
Classify up to 50 leads. Be conservative: reject or route away if the source is only an individual paper, method paper, or irrelevant false positive.
Each decision will later become a per-lead receipt file, so future cue builds can skip reviewed items by target-file existence.

The user will save your JSON as: `steps/review_cue/figure1_search_leads/reviewcue-decisions-figure1_search_leads-gpt-batch001.json`

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

21. review_id: review_figure1_search_leads_dda29ca9aa76
   lead_key: title:analyzing_data_of_a_multilab_replication_project_with_individual_participant_data_meta_analysis
   queue_status: needs_root_candidate_review
   name: Analyzing Data of a Multilab Replication Project With Individual Participant Data Meta-Analysis
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1027/2151-2604/a000483
   source_key: 10.1027/2151-2604/a000483 | https://openalex.org/W4210766447
   description: <jats:p>Abstract. Multilab replication projects such as Registered Replication Reports (RRR) and Many Labs projects are used to replicate an effect in different labs. Data of these projects are usually analyzed using conventional meta-analysis methods. This is certainly not the best approach because it does not make optimal use of the available data as a summary rather than participant data are analyzed. I propose to analyze data of multilab replication projects with individual participant data (IPD) meta-analysis where the participant data are analyzed directly. The prominent advantages of IPD meta-analysis are that it generally has larger statistical power to detect moderator effects and allows drawing conclusions at the participant and lab level. However, a disadvantage is that IPD meta-analysis is more complex than conventional meta-analysis. In this tutorial, I illustrate IPD meta-analysis using the RRR by McCarthy and colleagues, and I provide R code and recommendations to facilitate researchers to apply these methods.</jats:p>
   current heuristic reason: Matched Figure 1 bibliographic search query '"replication project" "coded data"'; lead_classification=corpus_database_or_project_signal; score=21; reasons=strong_phrase:replication project | strong_phrase:registered replication report | strong_phrase:many labs | data_term:data | data_term:code | replication_word | metadata_corpus_signal

22. review_id: review_figure1_search_leads_ce0d98ff2acc
   lead_key: title:analyzing_data_of_a_multilab_replication_project_with_individual_participant_data_meta_analysis_a_tutorial
   queue_status: needs_root_candidate_review
   name: Analyzing data of a multilab replication project with individual participant data meta-analysis: A tutorial
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.31222/osf.io/9tmua
   source_key: https://openalex.org/W3094282098 | 10.31222/osf.io/9tmua
   description: Multilab replication projects such as Registered Replication Reports (RRR) and Many Labs projects are used to replicate an effect in different labs. Data of these projects are usually analyzed using conventional meta-analysis methods. This is certainly not the best approach, because it does not make optimal use of the available data as summary rather than participant data are analyzed. I propose to analyze data of multilab replication projects with individual participant data (IPD) meta-analysis where the participant data are analyzed directly. Prominent advantages of IPD meta-analysis are that it generally has larger statistical power to detect moderator effects and allows drawing conclusions at the participant and lab level. However, a disadvantage is that IPD meta-analysis is more complex than conventional meta-analysis. In this tutorial, I illustrate IPD meta-analysis using the RRR by McCarthy and colleagues, and I provide R code and recommendations to facilitate researchers to apply these methods.
   current heuristic reason: Matched Figure 1 citation search query '"registered replication report" "many labs"'; lead_classification=corpus_database_or_project_signal; score=21; reasons=strong_phrase:replication project | strong_phrase:registered replication report | strong_phrase:many labs | data_term:data | data_term:code | replication_word | metadata_corpus_signal

23. review_id: review_figure1_search_leads_77bdfd624563
   lead_key: title:artificial_intelligence_in_psychology_research
   queue_status: needs_root_candidate_review
   name: Artificial intelligence in psychology research
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.31234/osf.io/rva3w
   source_key: https://openalex.org/W4321102425
   description: Large Language Models have vastly grown in capabilities. One potential application of such AI systems is to support data collection in the social sciences, where perfect experimental control is currently unfeasible and the collection of large, representative datasets is generally expensive. In this paper, we re-replicate 14 studies from the Many Labs 2 replication project (Klein et al., 2018) with OpenAI’s text-davinci-003 model, colloquially known as GPT3.5. For the 10 studies that we could analyse, we collected a total of 10,136 responses, each of which was obtained by running GPT3.5 with the corresponding study’s survey inputted as text. We find that our GPT3.5-based sample replicates 30% of the original results as well as 30% of the Many Labs 2 results, although there is heterogeneity in both these numbers (as we replicate some original findings that Many Labs 2 did not and vice versa). We also find that unlike the corresponding human subjects, GPT3.5 answered some survey questions with extreme homogeneity—with zero variation in different runs’ responses—raising concerns that a hypothetical AI-led future may in certain ways be subject to a diminished diversity of thought. Overall, while our results suggest that Large Language Model psychology studies are feasible, their findings should not be assumed to straightforwardly generalise to the human case. Nevertheless, AI-based data collection may eventually become a viable and economically relevant method in the empirical social sciences, making the understanding of its capabilities and applications central.
   current heuristic reason: Matched Figure 1 domain search query '"many-lab" dataset original'; lead_classification=corpus_database_or_project_signal; score=18; reasons=strong_phrase:replication project | strong_phrase:many labs | data_term:data | data_term:dataset | replication_word | original_word | metadata_corpus_signal

24. review_id: review_figure1_search_leads_f7268b4a35f7
   lead_key: title:author_response_investigating_the_replicability_of_preclinical_cancer_biology
   queue_status: needs_root_candidate_review
   name: Author response: Investigating the replicability of preclinical cancer biology
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.7554/elife.71601.sa2
   source_key: https://openalex.org/W4200021434
   description: Article Figures and data Abstract Introduction Results Discussion Materials and methods Data availability References Decision letter Author response Article and author information Metrics Abstract Replicability is an important feature of scientific research, but aspects of contemporary research culture, such as an emphasis on novelty, can make replicability seem less important than it should be. The Reproducibility Project: Cancer Biology was set up to provide evidence about the replicability of preclinical research in cancer biology by repeating selected experiments from high-impact papers. A total of 50 experiments from 23 papers were repeated, generating data about the replicability of a total of 158 effects. Most of the original effects were positive effects (136), with the rest being null effects (22). A majority of the original effect sizes were reported as numerical values (117), with the rest being reported as representative images (41). We employed seven methods to assess replicability, and some of these methods were not suitable for all the effects in our sample. One method compared effect sizes: for positive effects, the median effect size in the replications was 85% smaller than the median effect size in the original experiments, and 92% of replication effect sizes were smaller than the original. The other methods were binary – the replication was either a success or a failure – and five of these methods could be used to assess both positive and null effects when effect sizes were reported as numerical values. For positive effects, 40% of replications (39/97) su
   current heuristic reason: Matched Figure 1 citation search query '"Reproducibility Project: Cancer Biology" "effect size"'; lead_classification=corpus_database_or_project_signal; score=20; reasons=strong_phrase:reproducibility project | pair_term:original effect | pair_term:replication effect | pair_term:effect size | data_term:data | replication_word | original_word | effect_or_sample_size_phrase | metadata_corpus_signal

25. review_id: review_figure1_search_leads_4599c36edb44
   lead_key: title:bringing_an_intersectional_lens_to_open_science_an_analysis_of_representation_in_the_reproducibility_project
   queue_status: needs_root_candidate_review
   name: Bringing an Intersectional Lens to “Open” Science: An Analysis of Representation in the Reproducibility Project
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1177/03616843211035678
   source_key: 10.1177/03616843211035678
   description: <jats:p> Feminist psychologists have called for researchers to consider the social and historical context and the multidimensionality of participants in research studies. The Reproducibility Project documents the degree to which the findings from mainstream psychological studies are reproduced. Drawing on intersectionality theory, we question the value of reproducing findings while ignoring who is represented, intersecting social and group identities, sociohistorical context, and the power and privilege that likely influence participants’ responses in psychology experiments. To critically examine the Reproducibility Project in psychology, we analyzed the 100 replication reports produced between 2011 and 2014 (Open Science Collaboration, 2015). We developed an intersectional analytic framework to investigate (a) representation, (b) whether demographic and identity factors were considered through a multidimensional or intersectional lens, (c) explanations of non-replication, and (d) whether socio-cultural context was considered. Results show that reports predominantly include WEIRD samples (people from Western, educated, industrialized, rich, and democratic countries). Context and identity were rarely considered, even when study design relied on these factors, and intersectional identities and structures (considering power, structural issues, discrimination, and historical context) were absent from nearly all reports. Online slides for instructors who want to use this article f
   current heuristic reason: Matched Figure 1 citation search query '"Reproducibility Project: Psychology" "original study"'; lead_classification=corpus_database_or_project_signal; score=9; reasons=strong_phrase:reproducibility project | replication_word | metadata_corpus_signal

26. review_id: review_figure1_search_leads_f5860736bcb1
   lead_key: title:caballero_2021_replication_project
   queue_status: needs_root_candidate_review
   name: Caballero 2021 Replication Project
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://osf.io/kdbsa/
   source_key: kdbsa
   description: This project is a direct replication of Study 2 from Caballero et al. (2021), which examined whether experiencing economic scarcity leads individuals to adopt a more concrete (lower-level) construal style compared to those in conditions of economic sufficiency. The study uses the Bimboola economic-scarcity manipulation, assigning participants to imagine living in either a highly resource-constrained economic group or a financially comfortable group. Construal level is assessed using the Behavioral Identification Form (BIF; Vallacher &amp; Wegner, 1989), administered both before and after the economic manipulation to capture within-person changes in abstraction. The purpose of the replication is to evaluate whether the original finding, namely a significant interaction between time (pre–post) and economic condition (scarcity vs. nonscarcity), can be reproduced in a U.S.-based online sample recruited through Prolific. According to the original study, participants assigned to economic scarcity showed a decrease in abstract construal after the manipulation, whereas participants assigned to nonscarcity showed an increase. No baseline differences in construal level were observed prior to the manipulation. The planned replication follows the original procedure as closely as possible: participants complete 12 BIF items at baseline, complete the Bimboola assignment with stimuli adapted for online presentation, and then complete another 12 BIF items. Manipulation checks assessing perceived poverty and wealth of one’s assigned group are also included, mirroring the original study to c
   current heuristic reason: Matched Figure 1 repository search query '"replication project" "coded data" "original study"'; lead_classification=corpus_database_or_project_signal; score=11; reasons=strong_phrase:replication project | pair_term:original study | replication_word | original_word

27. review_id: review_figure1_search_leads_ed3a377a1fcd
   lead_key: title:can_cancer_researchers_accurately_judge_whether_preclinical_reports_will_reproduce
   queue_status: needs_root_candidate_review
   name: Can cancer researchers accurately judge whether preclinical reports will reproduce?
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1371/journal.pbio.2002212
   source_key: https://openalex.org/W2732894280
   description: There is vigorous debate about the reproducibility of research findings in cancer biology. Whether scientists can accurately assess which experiments will reproduce original findings is important to determining the pace at which science self-corrects. We collected forecasts from basic and preclinical cancer researchers on the first 6 replication studies conducted by the Reproducibility Project: Cancer Biology (RP:CB) to assess the accuracy of expert judgments on specific replication outcomes. On average, researchers forecasted a 75% probability of replicating the statistical significance and a 50% probability of replicating the effect size, yet none of these studies successfully replicated on either criterion (for the 5 studies with results reported). Accuracy was related to expertise: experts with higher h-indices were more accurate, whereas experts with more topic-specific expertise were less accurate. Our findings suggest that experts, especially those with specialized knowledge, were overconfident about the RP:CB replicating individual experiments within published reports; researcher optimism likely reflects a combination of overestimating the validity of original studies and underestimating the difficulties of repeating their methodologies.
   current heuristic reason: Matched Figure 1 bibliographic search query '"reproducibility project" "effect sizes"'; lead_classification=corpus_database_or_project_signal; score=22; reasons=strong_phrase:reproducibility project | strong_phrase:replication studies | pair_term:original studies | pair_term:effect size | replication_word | original_word | effect_or_sample_size_phrase | metadata_corpus_signal

28. review_id: review_figure1_search_leads_75bf3c17e235
   lead_key: title:can_large_language_models_replace_human_subjects_a_large_scale_replication_of_scenario_based_experiments_in_psychology_a
   queue_status: needs_root_candidate_review
   name: Can Large Language Models Replace Human Subjects? A Large-Scale Replication of Scenario-Based Experiments in Psychology and Management
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://springernature.figshare.com/articles/dataset/Can_Large_Language_Models_Replace_Human_Subjects_A_Large-Scale_Replication_of_Scenario-Based_Experiments_in_Psychology_and_Management/27157524/1 | https://springernature.figshare.com/articles/dataset/Can_Large_Language_Models_Replace_Human_Subjects_A_Large-Scale_Replication_of_Scenario-Based_Experiments_in_Psychology_and_Management/27157524
   source_key: 10.6084/m9.figshare.27157524.v1 | 10.6084/m9.figshare.27157524
   description: This repository contains data and code for a research project replicating human psychological experiments using Large Language Models (LLMs). The project systematically evaluates how GPT-4, Claude, and DeepSeek respond to the same experimental conditions as human participants across multiple psychological studies. ## Project Overview This research investigates whether LLMs can replicate results from human psychological experiments. By presenting LLMs with identical experimental conditions used in the original studies, we compare LLM responses with human responses to assess their understanding of human psychology and potential utility as research tools. Models used in this research: - **GPT-4**: Default temperature of 1.0, with additional analyses at temperatures 0 and 0.5 - **Claude**: Default temperature settings - **DeepSeek**: Temperature set to 1.3 (optimized for conversational scenarios) ## Repository Structure The repository is organized into three main directories: ### 1. LLM API Calls (01 LLM API Calls) Contains code and documentation for making API calls to different LLM models: - **prompt/**: Prompts used to query the LLMs - **script/**: Scripts for making API calls (`script_gpt.py`, `script_gpt_image.py`, `script_claude.py`, etc.) - **output data/**: Raw output data from the LLM API calls - **README_LLMs API Calls.docx**: Documentation for the API call process ### 2. Study-level Analysis (02 Study-level analysis) Contains individual analyses for each replicated study. Each study folder follows the naming convention `[Journal]_[Paper]_[Study]`, where: - Journal: O
   current heuristic reason: Matched Figure 1 link_graph search query '10.1038/s43588-025-00840-7'; lead_classification=corpus_database_or_project_signal; score=18; reasons=strong_phrase:large-scale replication | pair_term:original studies | data_term:data | data_term:code | data_term:repository | replication_word | original_word | known_corpus_paper_link_graph

29. review_id: review_figure1_search_leads_3b461705e061
   lead_key: title:cancer_reproducibility_project_scales_back_ambitions
   queue_status: needs_root_candidate_review
   name: Cancer reproducibility project scales back ambitions
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1038/nature.2015.18938
   source_key: 10.1038/nature.2015.18938
   description: 
   current heuristic reason: Matched Figure 1 bibliographic search query '"reproducibility project" "effect sizes"'; lead_classification=corpus_database_or_project_signal; score=7; reasons=strong_phrase:reproducibility project | metadata_corpus_signal

30. review_id: review_figure1_search_leads_62a5c00b9ba8
   lead_key: title:challenges_and_suggestions_for_defining_replication_success_when_effects_may_be_heterogeneous_comment_on_hedges_and_scha
   queue_status: needs_root_candidate_review
   name: Challenges and suggestions for defining replication “success” when effects may be heterogeneous: Comment on Hedges and Schauer (2019).
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1037/met0000223
   source_key: https://openalex.org/W2979112662
   description: Psychological scientists are now trying to replicate published research from scratch to confirm the findings. In an increasingly widespread replication study design, each of several collaborating sites (such as universities) independently tries to replicate an original study, and the results are synthesized across sites. Hedges and Schauer (2019) proposed statistical analyses for these replication projects; their analyses focus on assessing the extent to which results differ across the replication sites, by testing for heterogeneity among a set of replication studies, while excluding the original study. We agree with their premises regarding the limitations of existing analysis methods and regarding the importance of accounting for heterogeneity among the replications. This objective may be interesting in its own right. However, we argue that by focusing only on whether the replication studies have similar effect sizes to one another, these analyses are not particularly appropriate for assessing whether the replications in fact support the scientific effect under investigation or for assessing the power of multisite replication projects. We reanalyze Hedges and Schauer's (2019) example dataset using alternative metrics of replication success that directly address these objectives. We reach a more optimistic conclusion regarding replication success than they did, illustrating that the alternative metrics can lead to quite different conclusions from those of Hedges and Schauer (2019). (PsycINFO Database Record (c) 2019 APA, all rights reserved).
   current heuristic reason: Matched Figure 1 bibliographic search query '"replication project" "original study" "effect size"'; lead_classification=corpus_database_or_project_signal; score=23; reasons=strong_phrase:replication project | strong_phrase:replication studies | pair_term:original study | pair_term:effect size | data_term:data | data_term:dataset | data_term:database | replication_word | original_word | metadata_corpus_signal

31. review_id: review_figure1_search_leads_6061ab8657b3
   lead_key: title:comparing_meta_analyses_and_pre_registered_multiple_labs_replication_projects
   queue_status: needs_root_candidate_review
   name: Comparing Meta-Analyses and Pre-Registered Multiple Labs Replication Projects
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.31219/osf.io/brzwt
   source_key: https://openalex.org/W4229834291
   description: Many researchers rely on meta-analysis to summarize research evidence. However, recent replication projects in the behavioral sciences suggest that effect sizes of original studies are overestimated, and this overestimation is typically attributed to publication bias and selective reporting of scientific results. As the validity of meta-analyses depends on the primary studies, there is a concern that systematic overestimation of effect sizes may translate into biased meta-analytic effect sizes. We compare the results of meta-analyses to large-scale pre-registered replications in psychology carried out at multiple labs. The multiple labs replications provide relatively precisely estimated effect sizes, which do not suffer from publication bias or selective reporting. Searching the literature, 17 meta-analyses – spanning more than 1,200 effect sizes and more than 370,000 participants - on the same topics as multiple labs replications are identified. We find that the meta-analytic effect sizes are significantly different from the replication effect sizes for 12 out of the 17 meta-replication pairs. These differences are systematic and on average meta-analytic effect sizes are about three times as large as the replication effect sizes.
   current heuristic reason: Matched Figure 1 bibliographic search query '"replication project" "original study" "effect size"'; lead_classification=corpus_database_or_project_signal; score=17; reasons=strong_phrase:replication project | pair_term:original studies | pair_term:replication effect | pair_term:effect size | replication_word | original_word | metadata_corpus_signal

32. review_id: review_figure1_search_leads_27d5775f87b9
   lead_key: title:compilation_of_diener_et_al_2010_osf_multi_site_replication_projects
   queue_status: needs_root_candidate_review
   name: Compilation of Diener et al. (2010) OSF Multi-Site Replication Projects
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://osf.io/qdx7p/
   source_key: qdx7p
   description: OSF page consists of the data from the Diener et al. (2010) replication datasets that exist and are available on OSF. This page is also home to the analysis that the original researchers conducted at the University of Minnesota - Twin Cities. We hope that others can use this data and benefit from OSF.
   current heuristic reason: Matched Figure 1 domain search query '"multi-site" replication dataset original'; lead_classification=corpus_database_or_project_signal; score=20; reasons=strong_phrase:replication project | strong_phrase:multi-site replication | data_term:data | data_term:dataset | data_term:osf | replication_word | original_word | repository_data_surface | metadata_corpus_signal

33. review_id: review_figure1_search_leads_3bb59d13d306
   lead_key: title:confounds_in_failed_replications
   queue_status: needs_root_candidate_review
   name: Confounds in “failed” replications
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.31234/osf.io/gth8u
   source_key: https://openalex.org/W4238249240
   description: Reproducibility is essential to science, yet a distressingly large number of research findings do not seem to replicate. Here I discuss one underappreciated reason for this state of affairs. I make my case by noting that, due to artifacts, several of the replication failures of the vastly advertised Open Science Collaboration’s Reproducibility Project: Psychology turned out to be invalid. Although these artifacts would have been obvious on perusal of the data, such perusal was deemed undesirable because of its post hoc nature and was left out. However, while data do not lie, unforeseen confounds can render them unable to speak to the question of interest. I look further into one unusual case in which a major artifact could be removed statistically—the nonreplication of the effect of fertility on partnered women’s preference for single over attached men. I show that the “failed replication” datasets contain a gross bias in stimulus allocation which is absent in the original dataset; controlling for it replicates the original study’s main finding. I conclude that, before being used to make a scientific point, all data should undergo a minimal quality control—a provision, it appears, not always required of those collected for purpose of replication. Because unexpected confounds and biases can be laid bare only after the fact, we must get over our understandable reluctance to engage in anything post hoc. The reproach attached to p-hacking cannot exempt us from the obligation to (openly) take a good look at our data.
   current heuristic reason: Matched Figure 1 citation search query '"Reproducibility Project: Psychology" dataset replication'; lead_classification=corpus_database_or_project_signal; score=15; reasons=strong_phrase:reproducibility project | pair_term:original study | data_term:data | data_term:dataset | replication_word | original_word | metadata_corpus_signal

34. review_id: review_figure1_search_leads_7d6514b80c79
   lead_key: title:construct_validity_and_the_validity_of_replication_studies_a_systematic_review
   queue_status: needs_root_candidate_review
   name: Construct validity and the validity of replication studies: A systematic review.
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1037/amp0001006 | https://doi.org/10.31234/osf.io/369qj
   source_key: https://openalex.org/W4225083776 | https://openalex.org/W4221089041
   description: Currently, there is little guidance for navigating measurement challenges that threaten construct validity in replication research. To identify common challenges and ultimately strengthen replication research, we conducted a systematic review of the measures used in the 100 original and replication studies from the Reproducibility Project: Psychology (Open Science Collaboration, 2015). Results indicate that it was common for scales used in the original studies to have little or no validity evidence. Our systematic review demonstrates and corroborates evidence that issues of construct validity are sorely neglected in original and replicated research. We identify four measurement challenges replicators are likely to face: a lack of essential measurement information, a lack of validity evidence, measurement differences, and translation. Next, we offer solutions for addressing these challenges that will improve measurement practices in original and replication research. Finally, we close with a discussion of the need to develop measurement methodologies for the next generation of replication research. (PsycInfo Database Record (c) 2022 APA, all rights reserved).
   current heuristic reason: Matched Figure 1 citation search query '"Reproducibility Project: Psychology" "original study"'; lead_classification=corpus_database_or_project_signal; score=20; reasons=strong_phrase:reproducibility project | strong_phrase:replication studies | pair_term:original studies | data_term:data | data_term:database | replication_word | original_word | metadata_corpus_signal

35. review_id: review_figure1_search_leads_09abed40d362
   lead_key: title:corpus_suggestion_tracker
   queue_status: needs_root_candidate_review
   name: corpus suggestion tracker
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: reports/corpus_suggestion_tracker.md
   source_key: reports/corpus_suggestion_tracker.md
   description: Local scan hit; file_type=text_or_code; matched_query=study_pair_id original replication; path=reports/corpus_suggestion_tracker.md; snippet=1,969 original-claim rows across 762 original-paper DOI units. Paper-level slope `-0.421`; p<.10 share about 94%. | Not a random journal-paper sample. Rows are original findings selected into replication projects/databases or submitted as replications, so this is a replication-target/focal-claim frame. Not all rows are treatment/intervention effects. | Audit effect-type conversions, especially p-only and et
   current heuristic reason: Matched Figure 1 code search query 'study_pair_id original replication'; lead_classification=corpus_database_or_project_signal; score=13; reasons=strong_phrase:replication project | data_term:data | data_term:database | data_term:code | replication_word | original_word | query_phrase_in_text

36. review_id: review_figure1_search_leads_53d32984a608
   lead_key: title:cross_platform_metabolomics_imputation_using_importance_weighted_autoencoders
   queue_status: needs_root_candidate_review
   name: Cross-platform metabolomics imputation using importance-weighted autoencoders
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1101/2025.03.06.25323475 | https://doi.org/10.1038/s41540-025-00644-5
   source_key: https://doi.org/10.1101/2025.03.06.25323475 | PMC12894875
   description: <h4>Background</h4> Metabolomics data are often generated through different analytical platforms and different methods of identification and quantification which makes their synthesis and large-scale replication challenging. To address this, we applied generative deep learning to impute metabolites assayed by Metabolon, a commonly used commercial platform, using metabolomic features acquired by an untargeted liquid chromatography-mass spectrometry (LC-MS) platform. <h4>Methods</h4> We utilised a subset of 979 samples from the Airwave Health Monitoring Study which were assayed by both Metabolon and National Phenome Centre at Imperial College (NPC) LC-MS assays to develop an ensemble of importance-weighted autoencoders (IWAEs) which can perform cross-platform metabolomics imputation between the two assays. Using the ensemble, we generated a Metabolon equivalent dataset in 2,971 additional Airwave samples that lacked prior Metabolon measurements. We conducted observational associations with two clinical outcomes, body mass index (BMI) and C-reactive protein (CRP). We validated the ensemble and imputed data by investigating the concordance of the observational associations. This was done using both the imputed Metabolon dataset and the measured metabolite levels by Metabolon, and NPC in the Airwave study and Nightingale platform in the UK Biobank. <h4>Results</h4> Our imputation ensemble generated samples highly correlated with their real values across all Metabolon metabolites within a held-out test set with a mean sample correlation of 0.61 (IQR 0.55-0.67). The well-imputed s
   current heuristic reason: Matched Figure 1 bibliographic search query '"large-scale replication" "dataset"'; lead_classification=corpus_database_or_project_signal; score=12; reasons=strong_phrase:large-scale replication | data_term:data | data_term:dataset | data_term:code | replication_word | metadata_corpus_signal

37. review_id: review_figure1_search_leads_c003e8bf12be
   lead_key: title:data_from_investigating_variation_in_replicability_a_many_labs_replication_project
   queue_status: needs_root_candidate_review
   name: Data from Investigating Variation in Replicability: A “Many Labs” Replication Project
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.5334/jopd.ad | https://doi.org/10.31234/osf.io/25ju4
   source_key: 10.5334/jopd.ad | https://openalex.org/W2126632863 | https://openalex.org/W4226251881
   description: 
   current heuristic reason: Matched Figure 1 bibliographic search query '"replication project" "coded data"'; lead_classification=corpus_database_or_project_signal; score=15; reasons=strong_phrase:replication project | strong_phrase:many labs | data_term:data | replication_word | metadata_corpus_signal

38. review_id: review_figure1_search_leads_7f8c8d6ea1da
   lead_key: title:data_from_evaluating_the_foraging_performance_of_individual_honey_bees_in_different_environments_with_automated_field_rf
   queue_status: needs_root_candidate_review
   name: Data from: Evaluating the foraging performance of individual honey bees in different environments with automated field RFID systems
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.5061/dryad.83bk3j9s6
   source_key: doi:10.5061/dryad.83bk3j9s6
   description: <p style="margin-bottom:11px;text-align:left;">Measuring the individual foraging performances of pollinators is crucial to guide environmental policies that aim at enhancing pollinator health and pollination services. Automated systems have been developed to track the activity of individual honey bees, but their deployment is extremely challenging. This has limited the assessment of individual foraging performances in full-strength bee colonies in the field. Most studies available to date have been constrained to use downsized bee colonies located in urban and suburban areas. Environmental policy-making, on the other hand, needs a more comprehensive assessment of honey bee performances in a broader range of environments, including in remote agricultural and wild areas. Here we detail a new autonomous field method to record high quality data on the flight ontogeny and foraging performance of honey bees, using Radio-Frequency Identification (RFID). We separate bee traffic into returning and exiting tunnels to improve data quality, solving many previous limitations of RFID systems caused by traffic jams and the parasitic coupling of RFID antennae. With this method, we assembled a large RFID dataset made of control bee colonies from experiments conducted in different locations and seasons. We hope our results will be a starting point to understand how ontogenetic and environmental factors affect the individual performances of honey bees, and that our method will enable the large-scale replication of individual pollinator performance studies.</p>
   current heuristic reason: Matched Figure 1 repository search query '"large-scale replication" "data"'; lead_classification=corpus_database_or_project_signal; score=10; reasons=strong_phrase:large-scale replication | data_term:data | data_term:dataset | replication_word | dataset_metadata_surface

39. review_id: review_figure1_search_leads_0a55b6cc7790
   lead_key: title:die_vertrauensw_rdigkeit_von_replikationen_der_einfluss_von_pr_registrierungen_auf_den_replikationserfolg
   queue_status: needs_root_candidate_review
   name: Die Vertrauenswürdigkeit von Replikationen : Der Einfluss von Präregistrierungen auf den Replikationserfolg
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.20378/irb-105013
   source_key: https://openalex.org/W4405610981
   description: Theorie: Die Psychologie befindet sich in einer Replikationskrise, die unter anderem auf die „Publish or Perish“ Kultur zurückzuführen ist. Diese Kultur führt dazu, dass in großer Anzahl spannende und signifikante Studien veröffentlicht werden müssen, um im akademischen System Anerkennung zu finden. P-Hacking und andere fragwürdige Forschungspraktiken sind Auswirkungen dieser Kultur. In der vorliegenden Studie wurde untersucht, ob Replikationsstudien ebenfalls von Hacking betroffen sind. Es wurden dazu verschiedene Anreize für das Manipulieren von Replikationen vorgestellt. Besonders wurde auf Null-Hacking eingegangen, das durch die hohe Aufmerksamkeit auf nicht replizierte Befunde, begünstigt werden könnte. Methodik: Die Methode Präregistrierung gilt als ein direktes Mittel, um Freiheitsgrade von Forschenden einzuschränken und dabei Hacking entgegenzuwirken. Daher untersuchte die vorliegende präregistrierte Studie anhand der bisher umfassendsten Replikationsdatenbank (FORRT Replication Database), ob der Präregistrierungsstatus der Replikationsstudie den Zusammenhang zwischen Originaleffekt und Replikationseffekt moderiert. Nach allen Exklusionen wurden 361 Replikationseffekte berücksichtigt, von denen 124 präregistriert waren. Es wurde darüber hinaus ermittelt, ob die Ähnlichkeit (Closeness) zwischen der Originalstudie und der Replikationsstudie sowie verschiedene Präregistrierungsvorlagen den Zusammenhang zwischen Originaleffekt und Replikationseffekt moderieren. Zudem wurde explorativ untersucht, ob präregistrierte Replikationen sich hinsichtlich des Replikationserfolgs
   current heuristic reason: Matched Figure 1 citation search query '"FORRT" "replication database"'; lead_classification=corpus_database_or_project_signal; score=12; reasons=strong_phrase:replication database | data_term:data | data_term:database | replication_word | metadata_corpus_signal | query_phrase_in_text

40. review_id: review_figure1_search_leads_958c630e6e83
   lead_key: title:does_expertise_matter_in_replication_an_examination_of_the_reproducibility_project_psychology
   queue_status: needs_root_candidate_review
   name: Does expertise matter in replication? An examination of the reproducibility project: Psychology
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1016/j.jesp.2016.07.003
   source_key: 10.1016/j.jesp.2016.07.003
   description: 
   current heuristic reason: Matched Figure 1 citation search query '"Reproducibility Project: Psychology" "original study"'; lead_classification=corpus_database_or_project_signal; score=9; reasons=strong_phrase:reproducibility project | replication_word | metadata_corpus_signal

41. review_id: review_figure1_search_leads_e2c9f63ac70c
   lead_key: title:does_high_variability_training_improve_the_learning_of_non_native_phoneme_contrasts_over_low_variability_training_a_repl
   queue_status: needs_root_candidate_review
   name: Does high variability training improve the learning of non-native phoneme contrasts over low variability training? A replication
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1016/j.jml.2022.104352
   source_key: https://openalex.org/W4285585316
   description: Acquiring non-native speech contrasts can be difficult. A seminal study by Logan, Lively and Pisoni (1991) established the effectiveness of phonetic training for improving non-native speech perception: Japanese learners of English were trained to perceive /r/-/l/ using minimal pairs over 15 training sessions. A pre/post-test design established learning and generalisation. In a follow-up study, Lively, Logan and Pisoni (1993) presented further evidence which suggested that talker variability in training stimuli was crucial in leading to greater generalisation. These findings have been very influential and “high variability phonetic training” is now a standard methodology in the field. However, while the general benefit of phonetic training is well replicated, the evidence for an advantage of high over lower variability training remains mixed. In a large-scale replication of the original studies using updated statistical analyses we test whether learners generalise more after phonetic training using multiple talkers over a single talker. We find that listeners learn in both multiple and single talker conditions. However, in training, we find no difference in how well listeners learn for high vs low variability training. When comparing generalisation to novel talkers after training in relation to pre-training accuracy, we find ambiguous evidence for a high-variability benefit over low-variability training: This means that if a high-variability benefit exists, the effect is much smaller than originally thought, such that it cannot be detected in our sample of 166 listeners.
   current heuristic reason: Matched Figure 1 bibliographic search query '"large-scale replication" "original study"'; lead_classification=corpus_database_or_project_signal; score=13; reasons=strong_phrase:large-scale replication | pair_term:original studies | replication_word | original_word | metadata_corpus_signal

42. review_id: review_figure1_search_leads_46613d3e6bc2
   lead_key: title:does_repetition_increase_perceived_truth_equally_for_conspiracy_and_trivia_statements_a_registered_replication_report
   queue_status: needs_root_candidate_review
   name: Does repetition increase perceived truth equally for conspiracy and trivia statements? A registered replication report.
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.3758/s13423-025-02836-w
   source_key: PMC12779699
   description: Repetition increases the perceived truth of information. This illusory truth effect is a well-documented and robust phenomenon. Although research has primarily focused on trivia statements, the effects of repetition on belief have also been identified for consequential statements such as fake news headlines. Moreover, research reveals repetition increases accuracy ratings for conspiracy statements. However, in past work, the illusory truth effect was smaller for conspiracy statements than trivia statements. This result raises the intriguing possibility that there is something unique about conspiracy statements relative to trivia statements that makes them more resistant to the effects of repetition. However, this difference in the illusory truth effect between conspiracy and trivia statements may be due to differences in baseline plausibility rather than anything specific about conspiracy statements. Overall, the conspiracy statements were seen as less plausible than the trivia statements (both true and false trivia statements) in the prior experiment. In this registered report, we examined the illusory truth effect for conspiracy and trivia statements using the same procedure as in previous research, but we matched the statements on baseline plausibility. In line with our hypothesis, the effect of repetition on perceived truth was similar for conspiracy and trivia statements when they were equally implausible (or plausible). Results from this study replicate the generality of the illusory truth effect to statements that can cause harm and suggest that the psychological eff
   current heuristic reason: Matched Figure 1 bibliographic search query '"registered replication report" "original study"'; lead_classification=corpus_database_or_project_signal; score=7; reasons=strong_phrase:registered replication report | replication_word

43. review_id: review_figure1_search_leads_5a6989d0ac69
   lead_key: title:earth_science_citation_replication_project
   queue_status: needs_root_candidate_review
   name: Earth Science Citation Replication Project
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://osf.io/u49zv/
   source_key: u49zv
   description: This registration describes the hypotheses to be tested and the methods planned to replicate White 2019 (https://crl.acrl.org/index.php/crl/article/view/16892/19368), a study of the publication and citation practices of Earth Science researchers. We propose a programmatic approach to scale White’s original study and apply similar methods to three additional universities in the United States.
   current heuristic reason: Matched Figure 1 repository search query '"replication project" "coded data" "original study"'; lead_classification=corpus_database_or_project_signal; score=11; reasons=strong_phrase:replication project | pair_term:original study | replication_word | original_word

44. review_id: review_figure1_search_leads_6c2f7ee495da
   lead_key: title:ecls_k_replication_project
   queue_status: needs_root_candidate_review
   name: ECLS-K Replication Project
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://osf.io/gvzwe/ | https://osf.io/hsgj2/
   source_key: gvzwe | hsgj2
   description: For ReScience X article
   current heuristic reason: Matched Figure 1 citation search query '"ReScience"'; lead_classification=corpus_database_or_project_signal; score=10; reasons=strong_phrase:replication project | replication_word | metadata_corpus_signal | query_phrase_in_text

45. review_id: review_figure1_search_leads_24788ac9a7b9
   lead_key: title:eleven_years_of_student_replication_projects_provide_evidence_on_the_correlates_of_replicability_in_psychology
   queue_status: needs_root_candidate_review
   name: Eleven years of student replication projects provide evidence on the correlates of replicability in psychology.
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1098/rsos.231240
   source_key: PMC10645069
   description: Cumulative scientific progress requires empirical results that are robust enough to support theory construction and extension. Yet in psychology, some prominent findings have failed to replicate, and large-scale studies suggest replicability issues are widespread. The identification of predictors of replication success is limited by the difficulty of conducting large samples of independent replication experiments, however: most investigations reanalyse the same set of 170 replications. We introduce a new dataset of 176 replications from students in a graduate-level methods course. Replication results were judged to be successful in 49% of replications; of the 136 where effect sizes could be numerically compared, 46% had point estimates within the prediction interval of the original outcome (versus the expected 95%). Larger original effect sizes and within-participants designs were especially related to replication success. Our results indicate that, consistent with prior reports, the robustness of the psychology literature is low enough to limit cumulative progress by student investigators.
   current heuristic reason: Matched Figure 1 bibliographic search query '"replication project" "coded data"'; lead_classification=corpus_database_or_project_signal; score=17; reasons=strong_phrase:replication project | pair_term:original effect | pair_term:effect size | data_term:data | data_term:dataset | replication_word | original_word | metadata_corpus_signal

46. review_id: review_figure1_search_leads_95434678b310
   lead_key: title:estimating_the_replicability_of_sports_and_exercise_science_research
   queue_status: needs_root_candidate_review
   name: Estimating the Replicability of Sports and Exercise Science Research.
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1007/s40279-025-02201-w
   source_key: PMC12513899 | https://openalex.org/W4411351188
   description: <h4>Background</h4>The replicability of sports and exercise research has not been assessed previously despite concerns about scientific practices within the field.<h4>Aim</h4>This study aims to provide an initial estimate of the replicability of applied sports and exercise science research published in quartile 1 journals (SCImago journal ranking for 2019 in the Sports Science subject category; www.scimagojr.com ) between 2016 and 2021.<h4>Methods</h4>A formalised selection protocol for this replication project was previously published. Voluntary collaborators were recruited, and studies were allocated in a stratified and randomised manner on the basis of equipment and expertise. Original authors were contacted to provide deidentified raw data, to review preregistrations and to provide methodological clarifications. A multiple inferential strategy was employed to analyse the replication data. The same analysis (i.e. F test or t test) was used to determine whether the replication effect size was statistically significant and in the same direction as the original effect size. Z-tests were used to determine whether the original and replication effect size estimates were compatible or significantly different in magnitude.<h4>Results</h4>In total, 25 replication studies were included for analysis. Of the 25, 10 replications used paired t tests, 1 used an independent t test and 14 used an analysis of variance (ANOVA) for the statistical analyses. In all, 7 (28%) studies demonstrated robust replicability, meeting all three validation criteria: achieving statistical significance (p
   current heuristic reason: Matched Figure 1 bibliographic search query '"replication project" "original study" "effect size"'; lead_classification=corpus_database_or_project_signal; score=25; reasons=strong_phrase:replication project | strong_phrase:replication studies | pair_term:original effect | pair_term:replication effect | pair_term:effect size | data_term:data | replication_word | original_word | effect_or_sample_size_phrase | metadata_corpus_signal

47. review_id: review_figure1_search_leads_12b18a2b607a
   lead_key: title:evaluating_meta_analysis_as_a_replication_success_measure
   queue_status: needs_root_candidate_review
   name: Evaluating meta-analysis as a replication success measure.
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1371/journal.pone.0308495
   source_key: PMC11633967
   description: <h4>Background</h4>The importance of replication in the social and behavioural sciences has been emphasized for decades. Various frequentist and Bayesian approaches have been proposed to qualify a replication study as successful or unsuccessful. One of them is meta-analysis. The focus of the present study is on the way meta-analysis functions as a replication success metric. To investigate this, original and replication studies that are part of two large-scale replication projects were used. For each original study, the probability of replication success was calculated using meta-analysis under different assumptions of the underlying population effect when replication results were unknown. The accuracy of the predicted overall replication success was evaluated once replication results became available using adjusted Brier scores.<h4>Results</h4>Our results showed that meta-analysis performed poorly when used as a replication success metric. In many cases, quantifying replication success using meta-analysis resulted in the conclusion where the replication was deemed a success regardless of the results of the replication study.<h4>Discussion</h4>We conclude that when using meta-analysis as a replication success metric, it has a relatively high probability of finding evidence in favour of a non-zero population effect even when it is zero. This behaviour largely results from the significance of the original study. Furthermore, we argue that there are fundamental reasons against using meta-analysis as a metric for replication success.
   current heuristic reason: Matched Figure 1 bibliographic search query '"replication success" "original study"'; lead_classification=corpus_database_or_project_signal; score=23; reasons=strong_phrase:replication project | strong_phrase:large-scale replication | strong_phrase:replication studies | pair_term:original study | replication_word | original_word | metadata_corpus_signal

48. review_id: review_figure1_search_leads_2822063673be
   lead_key: title:evidence_for_goal_and_mixed_evidence_for_false_belief_based_action_prediction_in_2_to_4_year_old_children_a_large_scale_
   queue_status: needs_root_candidate_review
   name: Evidence for goal‐ and mixed evidence for false belief‐based action prediction in 2‐ to 4‐year‐old children: A large‐scale longitudinal anticipatory looking replication study
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1111/desc.13224
   source_key: https://openalex.org/W4200361560
   description: Unsuccessful replication attempts of paradigms assessing children's implicit tracking of false beliefs have instigated the debate on whether or not children have an implicit understanding of false beliefs before the age of four. A novel multi-trial anticipatory looking false belief paradigm yielded evidence of implicit false belief reasoning in 3- to 4-year-old children using a combined score of two false belief conditions (Grosse Wiesmann, C., Friederici, A. D., Singer, T., & Steinbeis, N. [2017]. Developmental Science, 20(5), e12445). The present study is a large-scale replication attempt of this paradigm. The task was administered three times to the same sample of N = 185 children at 2, 3, and 4 years of age. Using the original stimuli, we did not replicate the original finding of above-chance belief-congruent looking in a combined score of two false belief conditions in either of the three age groups. Interestingly, the overall pattern of results was comparable to the original study. Post-hoc analyses revealed, however, that children performed above chance in one false belief condition (FB1) and below chance in the other false belief condition (FB2), thus yielding mixed evidence of children's false belief-based action predictions. Similar to the original study, participants' performance did not change with age and was not related to children's general language skills. This study demonstrates the importance of large-scaled replications and adds to the growing number of research questioning the validity and reliability of anticipatory looking false belief paradigms as a r
   current heuristic reason: Matched Figure 1 bibliographic search query '"large-scale replication" "original study"'; lead_classification=corpus_database_or_project_signal; score=13; reasons=strong_phrase:large-scale replication | pair_term:original study | replication_word | original_word | metadata_corpus_signal

49. review_id: review_figure1_search_leads_3c4dddb6790c
   lead_key: title:evidence_for_infant_directed_speech_preference_is_consistent_across_large_scale_multi_site_replication_and_meta_analysis
   queue_status: needs_root_candidate_review
   name: Evidence for Infant-directed Speech Preference Is Consistent Across Large-scale, Multi-site Replication and Meta-analysis.
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1162/opmi_a_00134
   source_key: PMC11045035
   description: There is substantial evidence that infants prefer infant-directed speech (IDS) to adult-directed speech (ADS). The strongest evidence for this claim has come from two large-scale investigations: i) a community-augmented meta-analysis of published behavioral studies and ii) a large-scale multi-lab replication study. In this paper, we aim to improve our understanding of the IDS preference and its boundary conditions by combining and comparing these two data sources across key population and design characteristics of the underlying studies. Our analyses reveal that both the meta-analysis and multi-lab replication show moderate effect sizes (<i>d</i> ≈ 0.35 for each estimate) and that both of these effects persist when relevant study-level moderators are added to the models (i.e., experimental methods, infant ages, and native languages). However, while the overall effect size estimates were similar, the two sources diverged in the effects of key moderators: both infant age and experimental method predicted IDS preference in the multi-lab replication study, but showed no effect in the meta-analysis. These results demonstrate that the IDS preference generalizes across a variety of experimental conditions and sampling characteristics, while simultaneously identifying key differences in the empirical picture offered by each source individually and pinpointing areas where substantial uncertainty remains about the influence of theoretically central moderators on IDS preference. Overall, our results show how meta-analyses and multi-lab replications can be used in tandem to understand
   current heuristic reason: Matched Figure 1 bibliographic search query '"multi-lab replication" "original study"'; lead_classification=corpus_database_or_project_signal; score=14; reasons=strong_phrase:multi-site replication | pair_term:effect size | data_term:data | replication_word | effect_or_sample_size_phrase | metadata_corpus_signal

50. review_id: review_figure1_search_leads_c7808e6c3826
   lead_key: title:examining_the_replicability_of_online_experiments_selected_by_a_decision_market
   queue_status: needs_root_candidate_review
   name: Examining the replicability of online experiments selected by a decision market.
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1038/s41562-024-02062-9
   source_key: PMC11860227
   description: Here we test the feasibility of using decision markets to select studies for replication and provide evidence about the replicability of online experiments. Social scientists (n = 162) traded on the outcome of close replications of 41 systematically selected MTurk social science experiments published in PNAS 2015-2018, knowing that the 12 studies with the lowest and the 12 with the highest final market prices would be selected for replication, along with 2 randomly selected studies. The replication rate, based on the statistical significance indicator, was 83% for the top-12 and 33% for the bottom-12 group. Overall, 54% of the studies were successfully replicated, with replication effect size estimates averaging 45% of the original effect size estimates. The replication rate varied between 54% and 62% for alternative replication indicators. The observed replicability of MTurk experiments is comparable to that of previous systematic replication projects involving laboratory experiments.
   current heuristic reason: Matched Figure 1 bibliographic search query '"replication project" "original study" "effect size"'; lead_classification=corpus_database_or_project_signal; score=19; reasons=strong_phrase:replication project | pair_term:original effect | pair_term:replication effect | pair_term:effect size | replication_word | original_word | effect_or_sample_size_phrase | metadata_corpus_signal

```
