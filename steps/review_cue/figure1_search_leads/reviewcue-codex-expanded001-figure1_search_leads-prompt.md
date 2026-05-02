# figure1_search_leads Codex Review Prompt

Save returned JSON as `steps/review_cue/figure1_search_leads/reviewcue-decisions-figure1_search_leads-codex-expanded001.json`.

```text
You are a Codex background reviewer for review cue `figure1_search_leads`.
Reusable bounded review queue for ambiguous Figure 1 corpus/database, repository-package, result-table, individual-paper, and context-source leads. Deterministic scripts should remove obvious duplicates and false positives first. Codex should investigate moderate batches and either make auditable decisions or emit compact GPT prompt requests for uncertain cases. GPT prompt batches can be larger because they are user-mediated review artifacts.

Work only this bounded batch. Investigate URLs and source metadata when useful.
Do not edit root tables. Return or save JSON decisions using the contract below.
Each accepted decision will later be applied as a per-lead receipt file, so future cue builds can skip it by checking for that target file.
If you are not confident, set decision to `needs_more_evidence` and include `user_gpt_prompt_request` with a compact prompt the user can give to GPT Pro.

Save decisions as: `steps/review_cue/figure1_search_leads/reviewcue-decisions-figure1_search_leads-codex-expanded001.json`

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
1. review_id: review_figure1_search_leads_f4f3c376d419
   lead_key: title:replication_package
   queue_status: needs_root_candidate_review
   name: Replication Package
   record_kind: candidate_repository_package
   inventory_status: needs_triage_search_lead
   url: https://doi.org/10.7910/DVN/KYJQPC
   source_key: doi:10.7910/DVN/KYJQPC
   description: We investigate the pass-through of a temporary value-added tax (VAT) cut on selected food products to consumer prices in Portugal. Exploiting a novel data set of daily online prices, we find that the VAT cut was fully transmitted to consumer prices, persisted throughout the policy duration, and prices returned to the pre-implementation trend after reversal. We discuss two potential mechanisms driving this result: the policy's salience to consumers in a high-inflation environment and the decline of producer prices when implemented. We estimate that the policy reduced the inflation rate by 0.68 percentage points on impact.
   current heuristic reason: Matched Figure 1 repository search query '"replication package" "original" "replication" "sample size"'; lead_classification=repository_hit_without_corpus_confirmation; score=4; reasons=data_term:data | replication_word | repository_data_surface

2. review_id: review_figure1_search_leads_1791596725b9
   lead_key: title:a_large_scale_in_silico_replication_of_ecological_and_evolutionary_studies
   queue_status: needs_root_candidate_review
   name: A large-scale in silico replication of ecological and evolutionary studies.
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1038/s41559-024-02530-5
   source_key: PMC11618063
   description: Despite the growing concerns about the replicability of ecological and evolutionary studies, no results exist from a field-wide replication project. We conduct a large-scale in silico replication project, leveraging cutting-edge statistical methodologies. Replicability is 30%-40% for studies with marginal statistical significance in the absence of selective reporting, whereas the replicability of studies presenting 'strong' evidence against the null hypothesis H<sub>0</sub> is >70%. The former requires a sevenfold larger sample size to reach the latter's replicability. We call for a change in planning, conducting and publishing research towards a transparent, credible and replicable ecology and evolution.
   current heuristic reason: Matched Figure 1 bibliographic search query '"replication project" "original study" "effect size"'; lead_classification=corpus_database_or_project_signal; score=15; reasons=strong_phrase:replication project | pair_term:sample size | pair_term:larger sample | replication_word | effect_or_sample_size_phrase | metadata_corpus_signal

3. review_id: review_figure1_search_leads_29d4d29c1ba2
   lead_key: title:a_large_scale_replication_of_scenario_based_experiments_in_psychology_and_management_using_large_language_models
   queue_status: needs_root_candidate_review
   name: A large-scale replication of scenario-based experiments in psychology and management using large language models
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1038/s43588-025-00840-7
   source_key: 10.1038/s43588-025-00840-7
   description: 
   current heuristic reason: Matched Figure 1 bibliographic search query '"large-scale replication" "dataset"'; lead_classification=corpus_database_or_project_signal; score=9; reasons=strong_phrase:large-scale replication | replication_word | metadata_corpus_signal

4. review_id: review_figure1_search_leads_ec299d9c57b4
   lead_key: title:a_multi_site_registered_replication_report_of_olson_amp_fazio_2001_implicit_attitude_formation_through_classical_conditi
   queue_status: needs_root_candidate_review
   name: A multi-site Registered Replication Report of Olson &amp; Fazio (2001) "Implicit Attitude Formation Through Classical Conditioning"
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://osf.io/3hjpf/
   source_key: 3hjpf
   description: NB nomenclature has changed over time: despite title of original article, "implicit" here refers to self-reported attitudes that were acquired in the absence of awareness/memory of the CS-US pairings (rather than classical conditioning procedures giving rise to implicit attitudes)
   current heuristic reason: Matched Figure 1 repository search query '"registered replication report" data'; lead_classification=corpus_database_or_project_signal; score=9; reasons=strong_phrase:registered replication report | replication_word | original_word

5. review_id: review_figure1_search_leads_6720e58edd1a
   lead_key: title:a_multilab_preregistered_replication_of_the_ego_depletion_effect
   queue_status: needs_root_candidate_review
   name: A Multilab Preregistered Replication of the Ego-Depletion Effect
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1177/1745691616652873
   source_key: https://openalex.org/W2499154041
   description: Good self-control has been linked to adaptive outcomes such as better health, cohesive personal relationships, success in the workplace and at school, and less susceptibility to crime and addictions. In contrast, self-control failure is linked to maladaptive outcomes. Understanding the mechanisms by which self-control predicts behavior may assist in promoting better regulation and outcomes. A popular approach to understanding self-control is the strength or resource depletion model. Self-control is conceptualized as a limited resource that becomes depleted after a period of exertion resulting in self-control failure. The model has typically been tested using a sequential-task experimental paradigm, in which people completing an initial self-control task have reduced self-control capacity and poorer performance on a subsequent task, a state known as ego depletion Although a meta-analysis of ego-depletion experiments found a medium-sized effect, subsequent meta-analyses have questioned the size and existence of the effect and identified instances of possible bias. The analyses served as a catalyst for the current Registered Replication Report of the ego-depletion effect. Multiple laboratories (k = 23, total N = 2,141) conducted replications of a standardized ego-depletion protocol based on a sequential-task paradigm by Sripada et al. Meta-analysis of the studies revealed that the size of the ego-depletion effect was small with 95% confidence intervals (CIs) that encompassed zero (d = 0.04, 95% CI [-0.07, 0.15]. We discuss implications of the findings for the ego-depletion eff
   current heuristic reason: Matched Figure 1 bibliographic search query '"registered replication report" "original study"'; lead_classification=corpus_database_or_project_signal; score=7; reasons=strong_phrase:registered replication report | replication_word

6. review_id: review_figure1_search_leads_434c463074a7
   lead_key: title:a_problem_in_theory_and_more_measuring_the_moderating_role_of_culture_in_many_labs_2
   queue_status: needs_root_candidate_review
   name: A Problem in Theory and More: Measuring the Moderating Role of Culture in Many Labs 2
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.31234/osf.io/hmnrx
   source_key: https://doi.org/10.31234/osf.io/hmnrx | https://openalex.org/W4319984852
   description: <p>The multi-site replication study, Many Labs 2 (ML2), attempted to test whether population, site and setting variability moderates the likelihood of replication and effect size. The analysis concluded that sample location and setting did not substantially affect the replicability of findings. In this paper, we raise several issues with the ML2 approach to adjudicating the effect of culture that cast doubt on this conclusion. These theoretical and methodological problems (pre-registered at https://osf.io/6exr4) involve the: (1) selection of studies and sample sites for replication that are not theory-driven, (2) sampling of mostly WEIRD people around the world, (3) conflation of participants’ cultural backgrounds with the country where the samples came from, (4) use of the WEIRD backronym by decomposing it into a scale, and (5) application of a mean split of that WEIRD variable. Moreover, simulations reveal strikingly low statistical power for detecting cultural influences in a multi-side study designed like ML2. We propose methodologies to address problems (3) to( 5) by re-analyzing the ML2 dataset using an alternative approach. These results suggest that tackling only some of the design problems is insufficient to overcome the underlying theoretical and methodological deficiencies. We conclude with specific recommendations for assessing the role of population variability in future multi-site studies that address evidentiary value and effect size.</p>
   current heuristic reason: Matched Figure 1 bibliographic search query '"multi-site replication" "dataset"'; lead_classification=corpus_database_or_project_signal; score=21; reasons=strong_phrase:many labs | strong_phrase:multi-site replication | pair_term:effect size | data_term:data | data_term:dataset | data_term:osf | replication_word | effect_or_sample_size_phrase | metadata_corpus_signal

7. review_id: review_figure1_search_leads_55a96c22e10c
   lead_key: title:a_scoping_review_on_metrics_to_quantify_reproducibility_a_multitude_of_questions_leads_to_a_multitude_of_metrics
   queue_status: needs_root_candidate_review
   name: A scoping review on metrics to quantify reproducibility: a multitude of questions leads to a multitude of metrics.
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1098/rsos.242076
   source_key: PMC12395386 | https://openalex.org/W4412464884
   description: Reproducibility is recognized as essential to scientific progress and integrity. Replication studies and large-scale replication projects, aiming to quantify different aspects of reproducibility, have become more common. Since no standardized approach to measuring reproducibility exists, a diverse set of metrics has emerged and a comprehensive overview is needed. We conducted a scoping review to identify large-scale replication projects that used metrics and methodological papers that proposed or discussed metrics. The project list was compiled by the authors. For the methodological papers, we searched Scopus, MedLine, PsycINFO and EconLit. Records were screened in duplicate against pre-defined inclusion criteria. Demographic information on included records and information on reproducibility metrics used, suggested or discussed was extracted. We identified 49 large-scale projects and 97 methodological papers and extracted 50 metrics. The metrics were characterized based on type (formulas and/or statistical models, frameworks, graphical representations, studies and questionnaires, algorithms), input required and appropriate application scenarios. Each metric addresses a distinct question. Our review provides a comprehensive resource in the form of a 'live', interactive table for future replication teams and meta-researchers, offering support in how to select the most appropriate metrics that are aligned with research questions and project goals.
   current heuristic reason: Matched Figure 1 bibliographic search query '"replication database" "original" "replication"'; lead_classification=corpus_database_or_project_signal; score=19; reasons=strong_phrase:replication project | strong_phrase:large-scale replication | strong_phrase:replication studies | replication_word | metadata_corpus_signal

8. review_id: review_figure1_search_leads_115f5ee33aea
   lead_key: title:absence_of_a_meaningful_effect_of_intranasal_oxytocin_on_trusting_behavior_a_registered_report_with_pooled_equivalence_t
   queue_status: needs_root_candidate_review
   name: Absence of a meaningful effect of intranasal oxytocin on trusting behavior: a registered report with pooled equivalence testing.
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1016/j.cortex.2026.03.006
   source_key: 41880977
   description: The neuropeptide oxytocin (OXT) is thought to modulate important aspects of prosocial behavior. In a seminal paper, Kosfeld et al. (2005) reported that intranasally administered OXT modulated trusting behavior in an economic trust game. Several attempts to conceptually replicate these findings yielded mixed results, which might be partly due to small sample sizes that can reduce the ability to detect, or reject, meaningful effects. We performed a large-scale replication (n = 211) of Kosfeld et al. (2005) with specific attention for small effects and subpopulations whose trusting behavior may be sensitive to OXT manipulations. Moreover, we conducted a pooled analysis of the two largest, recent, replications by merging our data with data from Declerck et al. (2020; n = 321). We found no evidence that intranasal OXT administration increases trusting behavior, neither in our data nor in the pooled dataset. While equivalence testing in our dataset was inconclusive, equivalence testing in the pooled dataset (n = 532) indicated that the effect of OXT administration on trusting behavior lies within a minimal range of effects, suggesting that the effect is too small to be of interest to (most) lab-based studies due to feasibility constraints of collecting data from larger samples required to reject smaller effect sizes. In addition, we found no evidence that OXT administration effects on trusting behavior are influenced by baseline trust, reward sensitivity, and punishment sensitivity. Our findings invite a critical evaluation of current methodology in OXT research and a reconsidera
   current heuristic reason: Matched Figure 1 bibliographic search query '"large-scale replication" "dataset"'; lead_classification=corpus_database_or_project_signal; score=18; reasons=strong_phrase:large-scale replication | pair_term:effect size | pair_term:sample size | pair_term:larger sample | data_term:data | data_term:dataset | data_term:osf | replication_word | metadata_corpus_signal

9. review_id: review_figure1_search_leads_b7d63ec6dc91
   lead_key: title:administering_a_victim_impact_curriculum_to_inmates_a_multi_site_replication
   queue_status: needs_root_candidate_review
   name: Administering a victim impact curriculum to inmates: a multi-site replication
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1080/1478601x.2015.1014037
   source_key: 10.1080/1478601x.2015.1014037
   description: 
   current heuristic reason: Matched Figure 1 bibliographic search query '"multi-site replication" "dataset"'; lead_classification=corpus_database_or_project_signal; score=9; reasons=strong_phrase:multi-site replication | replication_word | metadata_corpus_signal

10. review_id: review_figure1_search_leads_08428e8f58d8
   lead_key: title:advancing_the_cognitive_science_of_religion_through_replication_and_open_science
   queue_status: needs_root_candidate_review
   name: Advancing the Cognitive Science of Religion through Replication and Open Science
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1558/jcsr.39039
   source_key: https://openalex.org/W3096603764
   description: The Cognitive Science of Religion (CSR) is a relatively young but prolific field that has offered compelling insights into religious minds and practices. However, many empirical findings within this field are still preliminary and their reliability remains to be determined. In this paper, we first argue that it is crucial to critically evaluate the CSR literature and adopt open science practices and replication research in particular to move the field forward. Second, we highlight the outcomes of previous replications and make suggestions for future replication studies in the CSR, with a particular focus on neuroscience, developmental psychology, and qualitative research. Finally, we provide a “replication script” with advice on how to select, conduct, and organize replication research. Our approach is illustrated with a “glimpse behind the scenes” of the recently launched Cross-Cultural Religious Replication Project, in the hope of inspiring scholars of religion to embrace open science and replication in their own research.
   current heuristic reason: Matched Figure 1 citation search query '"Many Labs" "original study" -> cites:W3163230172'; lead_classification=corpus_database_or_project_signal; score=14; reasons=strong_phrase:replication project | strong_phrase:replication studies | replication_word | metadata_corpus_signal

11. review_id: review_figure1_search_leads_1a654f61e08b
   lead_key: title:an_open_investigation_of_the_reproducibility_of_cancer_biology_research
   queue_status: needs_root_candidate_review
   name: An open investigation of the reproducibility of cancer biology research
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.7554/elife.04333
   source_key: https://openalex.org/W2142148275
   description: It is widely believed that research that builds upon previously published findings has reproduced the original work. However, it is rare for researchers to perform or publish direct replications of existing results. The Reproducibility Project: Cancer Biology is an open investigation of reproducibility in preclinical cancer biology research. We have identified 50 high impact cancer biology articles published in the period 2010-2012, and plan to replicate a subset of experimental results from each article. A Registered Report detailing the proposed experimental designs and protocols for each subset of experiments will be peer reviewed and published prior to data collection. The results of these experiments will then be published in a Replication Study. The resulting open methodology and dataset will provide evidence about the reproducibility of high-impact results, and an opportunity to identify predictors of reproducibility.
   current heuristic reason: Matched Figure 1 citation search query '"SCORE" "scientific claims" "replication"'; lead_classification=corpus_database_or_project_signal; score=13; reasons=strong_phrase:reproducibility project | data_term:data | data_term:dataset | replication_word | original_word | metadata_corpus_signal

12. review_id: review_figure1_search_leads_d39d12c4d968
   lead_key: title:analysis_of_rare_parkinson_s_disease_variants_in_millions_of_people
   queue_status: needs_root_candidate_review
   name: Analysis of rare Parkinson’s disease variants in millions of people
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1038/s41531-023-00608-8
   source_key: https://openalex.org/W4390667162
   description: Although many rare variants have been reportedly associated with Parkinson's disease (PD), many have not been replicated or have failed to replicate. Here, we conduct a large-scale replication of rare PD variants. We assessed a total of 27,590 PD cases, 6701 PD proxies, and 3,106,080 controls from three data sets: 23andMe, Inc., UK Biobank, and AMP-PD. Based on well-known PD genes, 834 variants of interest were selected from the ClinVar annotated 23andMe dataset. We performed a meta-analysis using summary statistics of all three studies. The meta-analysis resulted in five significant variants after Bonferroni correction, including variants in GBA1 and LRRK2. Another eight variants are strong candidate variants for their association with PD. Here, we provide the largest rare variant meta-analysis to date, providing information on confirmed and newly identified variants for their association with PD using several large databases. Additionally we also show the complexities of studying rare variants in large-scale cohorts.
   current heuristic reason: Matched Figure 1 bibliographic search query '"large-scale replication" "dataset"'; lead_classification=corpus_database_or_project_signal; score=12; reasons=strong_phrase:large-scale replication | data_term:data | data_term:dataset | data_term:database | replication_word | metadata_corpus_signal

13. review_id: review_figure1_search_leads_dda29ca9aa76
   lead_key: title:analyzing_data_of_a_multilab_replication_project_with_individual_participant_data_meta_analysis
   queue_status: needs_root_candidate_review
   name: Analyzing Data of a Multilab Replication Project With Individual Participant Data Meta-Analysis
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1027/2151-2604/a000483
   source_key: 10.1027/2151-2604/a000483 | https://openalex.org/W4210766447
   description: <jats:p>Abstract. Multilab replication projects such as Registered Replication Reports (RRR) and Many Labs projects are used to replicate an effect in different labs. Data of these projects are usually analyzed using conventional meta-analysis methods. This is certainly not the best approach because it does not make optimal use of the available data as a summary rather than participant data are analyzed. I propose to analyze data of multilab replication projects with individual participant data (IPD) meta-analysis where the participant data are analyzed directly. The prominent advantages of IPD meta-analysis are that it generally has larger statistical power to detect moderator effects and allows drawing conclusions at the participant and lab level. However, a disadvantage is that IPD meta-analysis is more complex than conventional meta-analysis. In this tutorial, I illustrate IPD meta-analysis using the RRR by McCarthy and colleagues, and I provide R code and recommendations to facilitate researchers to apply these methods.</jats:p>
   current heuristic reason: Matched Figure 1 bibliographic search query '"replication project" "coded data"'; lead_classification=corpus_database_or_project_signal; score=21; reasons=strong_phrase:replication project | strong_phrase:registered replication report | strong_phrase:many labs | data_term:data | data_term:code | replication_word | metadata_corpus_signal

14. review_id: review_figure1_search_leads_ce0d98ff2acc
   lead_key: title:analyzing_data_of_a_multilab_replication_project_with_individual_participant_data_meta_analysis_a_tutorial
   queue_status: needs_root_candidate_review
   name: Analyzing data of a multilab replication project with individual participant data meta-analysis: A tutorial
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.31222/osf.io/9tmua
   source_key: https://openalex.org/W3094282098
   description: Multilab replication projects such as Registered Replication Reports (RRR) and Many Labs projects are used to replicate an effect in different labs. Data of these projects are usually analyzed using conventional meta-analysis methods. This is certainly not the best approach, because it does not make optimal use of the available data as summary rather than participant data are analyzed. I propose to analyze data of multilab replication projects with individual participant data (IPD) meta-analysis where the participant data are analyzed directly. Prominent advantages of IPD meta-analysis are that it generally has larger statistical power to detect moderator effects and allows drawing conclusions at the participant and lab level. However, a disadvantage is that IPD meta-analysis is more complex than conventional meta-analysis. In this tutorial, I illustrate IPD meta-analysis using the RRR by McCarthy and colleagues, and I provide R code and recommendations to facilitate researchers to apply these methods.
   current heuristic reason: Matched Figure 1 citation search query '"registered replication report" "many labs"'; lead_classification=corpus_database_or_project_signal; score=21; reasons=strong_phrase:replication project | strong_phrase:registered replication report | strong_phrase:many labs | data_term:data | data_term:code | replication_word | metadata_corpus_signal

15. review_id: review_figure1_search_leads_77bdfd624563
   lead_key: title:artificial_intelligence_in_psychology_research
   queue_status: needs_root_candidate_review
   name: Artificial intelligence in psychology research
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.31234/osf.io/rva3w
   source_key: https://openalex.org/W4321102425
   description: Large Language Models have vastly grown in capabilities. One potential application of such AI systems is to support data collection in the social sciences, where perfect experimental control is currently unfeasible and the collection of large, representative datasets is generally expensive. In this paper, we re-replicate 14 studies from the Many Labs 2 replication project (Klein et al., 2018) with OpenAI’s text-davinci-003 model, colloquially known as GPT3.5. For the 10 studies that we could analyse, we collected a total of 10,136 responses, each of which was obtained by running GPT3.5 with the corresponding study’s survey inputted as text. We find that our GPT3.5-based sample replicates 30% of the original results as well as 30% of the Many Labs 2 results, although there is heterogeneity in both these numbers (as we replicate some original findings that Many Labs 2 did not and vice versa). We also find that unlike the corresponding human subjects, GPT3.5 answered some survey questions with extreme homogeneity—with zero variation in different runs’ responses—raising concerns that a hypothetical AI-led future may in certain ways be subject to a diminished diversity of thought. Overall, while our results suggest that Large Language Model psychology studies are feasible, their findings should not be assumed to straightforwardly generalise to the human case. Nevertheless, AI-based data collection may eventually become a viable and economically relevant method in the empirical social sciences, making the understanding of its capabilities and applications central.
   current heuristic reason: Matched Figure 1 citation search query '"Many Labs" replication project dataset'; lead_classification=corpus_database_or_project_signal; score=18; reasons=strong_phrase:replication project | strong_phrase:many labs | data_term:data | data_term:dataset | replication_word | original_word | metadata_corpus_signal

16. review_id: review_figure1_search_leads_f7268b4a35f7
   lead_key: title:author_response_investigating_the_replicability_of_preclinical_cancer_biology
   queue_status: needs_root_candidate_review
   name: Author response: Investigating the replicability of preclinical cancer biology
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.7554/elife.71601.sa2
   source_key: https://openalex.org/W4200021434
   description: Article Figures and data Abstract Introduction Results Discussion Materials and methods Data availability References Decision letter Author response Article and author information Metrics Abstract Replicability is an important feature of scientific research, but aspects of contemporary research culture, such as an emphasis on novelty, can make replicability seem less important than it should be. The Reproducibility Project: Cancer Biology was set up to provide evidence about the replicability of preclinical research in cancer biology by repeating selected experiments from high-impact papers. A total of 50 experiments from 23 papers were repeated, generating data about the replicability of a total of 158 effects. Most of the original effects were positive effects (136), with the rest being null effects (22). A majority of the original effect sizes were reported as numerical values (117), with the rest being reported as representative images (41). We employed seven methods to assess replicability, and some of these methods were not suitable for all the effects in our sample. One method compared effect sizes: for positive effects, the median effect size in the replications was 85% smaller than the median effect size in the original experiments, and 92% of replication effect sizes were smaller than the original. The other methods were binary – the replication was either a success or a failure – and five of these methods could be used to assess both positive and null effects when effect sizes were reported as numerical values. For positive effects, 40% of replications (39/97) su
   current heuristic reason: Matched Figure 1 citation search query '"Reproducibility Project: Cancer Biology" "effect size"'; lead_classification=corpus_database_or_project_signal; score=20; reasons=strong_phrase:reproducibility project | pair_term:original effect | pair_term:replication effect | pair_term:effect size | data_term:data | replication_word | original_word | effect_or_sample_size_phrase | metadata_corpus_signal

17. review_id: review_figure1_search_leads_4599c36edb44
   lead_key: title:bringing_an_intersectional_lens_to_open_science_an_analysis_of_representation_in_the_reproducibility_project
   queue_status: needs_root_candidate_review
   name: Bringing an Intersectional Lens to “Open” Science: An Analysis of Representation in the Reproducibility Project
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1177/03616843211035678
   source_key: 10.1177/03616843211035678
   description: <jats:p> Feminist psychologists have called for researchers to consider the social and historical context and the multidimensionality of participants in research studies. The Reproducibility Project documents the degree to which the findings from mainstream psychological studies are reproduced. Drawing on intersectionality theory, we question the value of reproducing findings while ignoring who is represented, intersecting social and group identities, sociohistorical context, and the power and privilege that likely influence participants’ responses in psychology experiments. To critically examine the Reproducibility Project in psychology, we analyzed the 100 replication reports produced between 2011 and 2014 (Open Science Collaboration, 2015). We developed an intersectional analytic framework to investigate (a) representation, (b) whether demographic and identity factors were considered through a multidimensional or intersectional lens, (c) explanations of non-replication, and (d) whether socio-cultural context was considered. Results show that reports predominantly include WEIRD samples (people from Western, educated, industrialized, rich, and democratic countries). Context and identity were rarely considered, even when study design relied on these factors, and intersectional identities and structures (considering power, structural issues, discrimination, and historical context) were absent from nearly all reports. Online slides for instructors who want to use this article f
   current heuristic reason: Matched Figure 1 citation search query '"Reproducibility Project: Psychology" "original study"'; lead_classification=corpus_database_or_project_signal; score=9; reasons=strong_phrase:reproducibility project | replication_word | metadata_corpus_signal

18. review_id: review_figure1_search_leads_f5860736bcb1
   lead_key: title:caballero_2021_replication_project
   queue_status: needs_root_candidate_review
   name: Caballero 2021 Replication Project
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://osf.io/kdbsa/
   source_key: kdbsa
   description: This project is a direct replication of Study 2 from Caballero et al. (2021), which examined whether experiencing economic scarcity leads individuals to adopt a more concrete (lower-level) construal style compared to those in conditions of economic sufficiency. The study uses the Bimboola economic-scarcity manipulation, assigning participants to imagine living in either a highly resource-constrained economic group or a financially comfortable group. Construal level is assessed using the Behavioral Identification Form (BIF; Vallacher &amp; Wegner, 1989), administered both before and after the economic manipulation to capture within-person changes in abstraction. The purpose of the replication is to evaluate whether the original finding, namely a significant interaction between time (pre–post) and economic condition (scarcity vs. nonscarcity), can be reproduced in a U.S.-based online sample recruited through Prolific. According to the original study, participants assigned to economic scarcity showed a decrease in abstract construal after the manipulation, whereas participants assigned to nonscarcity showed an increase. No baseline differences in construal level were observed prior to the manipulation. The planned replication follows the original procedure as closely as possible: participants complete 12 BIF items at baseline, complete the Bimboola assignment with stimuli adapted for online presentation, and then complete another 12 BIF items. Manipulation checks assessing perceived poverty and wealth of one’s assigned group are also included, mirroring the original study to c
   current heuristic reason: Matched Figure 1 repository search query '"replication project" "coded data" "original study"'; lead_classification=corpus_database_or_project_signal; score=11; reasons=strong_phrase:replication project | pair_term:original study | replication_word | original_word

19. review_id: review_figure1_search_leads_ed3a377a1fcd
   lead_key: title:can_cancer_researchers_accurately_judge_whether_preclinical_reports_will_reproduce
   queue_status: needs_root_candidate_review
   name: Can cancer researchers accurately judge whether preclinical reports will reproduce?
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1371/journal.pbio.2002212
   source_key: https://openalex.org/W2732894280
   description: There is vigorous debate about the reproducibility of research findings in cancer biology. Whether scientists can accurately assess which experiments will reproduce original findings is important to determining the pace at which science self-corrects. We collected forecasts from basic and preclinical cancer researchers on the first 6 replication studies conducted by the Reproducibility Project: Cancer Biology (RP:CB) to assess the accuracy of expert judgments on specific replication outcomes. On average, researchers forecasted a 75% probability of replicating the statistical significance and a 50% probability of replicating the effect size, yet none of these studies successfully replicated on either criterion (for the 5 studies with results reported). Accuracy was related to expertise: experts with higher h-indices were more accurate, whereas experts with more topic-specific expertise were less accurate. Our findings suggest that experts, especially those with specialized knowledge, were overconfident about the RP:CB replicating individual experiments within published reports; researcher optimism likely reflects a combination of overestimating the validity of original studies and underestimating the difficulties of repeating their methodologies.
   current heuristic reason: Matched Figure 1 bibliographic search query '"reproducibility project" "effect sizes"'; lead_classification=corpus_database_or_project_signal; score=22; reasons=strong_phrase:reproducibility project | strong_phrase:replication studies | pair_term:original studies | pair_term:effect size | replication_word | original_word | effect_or_sample_size_phrase | metadata_corpus_signal

20. review_id: review_figure1_search_leads_3b461705e061
   lead_key: title:cancer_reproducibility_project_scales_back_ambitions
   queue_status: needs_root_candidate_review
   name: Cancer reproducibility project scales back ambitions
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1038/nature.2015.18938
   source_key: 10.1038/nature.2015.18938
   description: 
   current heuristic reason: Matched Figure 1 bibliographic search query '"reproducibility project" "effect sizes"'; lead_classification=corpus_database_or_project_signal; score=7; reasons=strong_phrase:reproducibility project | metadata_corpus_signal

```
