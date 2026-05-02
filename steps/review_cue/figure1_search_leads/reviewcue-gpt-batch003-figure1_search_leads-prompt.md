# figure1_search_leads Gpt Review Prompt

Save returned JSON as `steps/review_cue/figure1_search_leads/reviewcue-decisions-figure1_search_leads-gpt-batch003.json`.

```text
You are reviewing `figure1_search_leads` leads for a provenance pipeline.
Use web research if needed. Do not infer relevance from search terms alone.
Classify up to 50 leads. Be conservative: reject or route away if the source is only an individual paper, method paper, or irrelevant false positive.
Each decision will later become a per-lead receipt file, so future cue builds can skip reviewed items by target-file existence.

The user will save your JSON as: `steps/review_cue/figure1_search_leads/reviewcue-decisions-figure1_search_leads-gpt-batch003.json`

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
1. review_id: review_figure1_search_leads_e2c9f63ac70c
   lead_key: title:does_high_variability_training_improve_the_learning_of_non_native_phoneme_contrasts_over_low_variability_training_a_repl
   queue_status: needs_root_candidate_review
   name: Does high variability training improve the learning of non-native phoneme contrasts over low variability training? A replication
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1016/j.jml.2022.104352
   source_key: https://openalex.org/W4285585316
   description: Acquiring non-native speech contrasts can be difficult. A seminal study by Logan, Lively and Pisoni (1991) established the effectiveness of phonetic training for improving non-native speech perception: Japanese learners of English were trained to perceive /r/-/l/ using minimal pairs over 15 training sessions. A pre/post-test design established learning and generalisation. In a follow-up study, Lively, Logan and Pisoni (1993) presented further evidence which suggested that talker variability in training stimuli was crucial in leading to greater generalisation. These findings have been very influential and “high variability phonetic training” is now a standard methodology in the field. However, while the general benefit of phonetic training is well replicated, the evidence for an advantage of high over lower variability training remains mixed. In a large-scale replication of the original studies using updated statistical analyses we test whether learners generalise more after phonetic training using multiple talkers over a single talker. We find that listeners learn in both multiple and single talker conditions. However, in training, we find no difference in how well listeners learn for high vs low variability training. When comparing generalisation to novel talkers after training in relation to pre-training accuracy, we find ambiguous evidence for a high-variability benefit over low-variability training: This means that if a high-variability benefit exists, the effect is much smaller than originally thought, such that it cannot be detected in our sample of 166 listeners.
   current heuristic reason: Matched Figure 1 bibliographic search query '"large-scale replication" "original study"'; lead_classification=corpus_database_or_project_signal; score=13; reasons=strong_phrase:large-scale replication | pair_term:original studies | replication_word | original_word | metadata_corpus_signal

2. review_id: review_figure1_search_leads_46613d3e6bc2
   lead_key: title:does_repetition_increase_perceived_truth_equally_for_conspiracy_and_trivia_statements_a_registered_replication_report
   queue_status: needs_root_candidate_review
   name: Does repetition increase perceived truth equally for conspiracy and trivia statements? A registered replication report.
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.3758/s13423-025-02836-w
   source_key: PMC12779699
   description: Repetition increases the perceived truth of information. This illusory truth effect is a well-documented and robust phenomenon. Although research has primarily focused on trivia statements, the effects of repetition on belief have also been identified for consequential statements such as fake news headlines. Moreover, research reveals repetition increases accuracy ratings for conspiracy statements. However, in past work, the illusory truth effect was smaller for conspiracy statements than trivia statements. This result raises the intriguing possibility that there is something unique about conspiracy statements relative to trivia statements that makes them more resistant to the effects of repetition. However, this difference in the illusory truth effect between conspiracy and trivia statements may be due to differences in baseline plausibility rather than anything specific about conspiracy statements. Overall, the conspiracy statements were seen as less plausible than the trivia statements (both true and false trivia statements) in the prior experiment. In this registered report, we examined the illusory truth effect for conspiracy and trivia statements using the same procedure as in previous research, but we matched the statements on baseline plausibility. In line with our hypothesis, the effect of repetition on perceived truth was similar for conspiracy and trivia statements when they were equally implausible (or plausible). Results from this study replicate the generality of the illusory truth effect to statements that can cause harm and suggest that the psychological eff
   current heuristic reason: Matched Figure 1 bibliographic search query '"registered replication report" "original study"'; lead_classification=corpus_database_or_project_signal; score=7; reasons=strong_phrase:registered replication report | replication_word

3. review_id: review_figure1_search_leads_5a6989d0ac69
   lead_key: title:earth_science_citation_replication_project
   queue_status: needs_root_candidate_review
   name: Earth Science Citation Replication Project
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://osf.io/u49zv/
   source_key: u49zv
   description: This registration describes the hypotheses to be tested and the methods planned to replicate White 2019 (https://crl.acrl.org/index.php/crl/article/view/16892/19368), a study of the publication and citation practices of Earth Science researchers. We propose a programmatic approach to scale White’s original study and apply similar methods to three additional universities in the United States.
   current heuristic reason: Matched Figure 1 repository search query '"replication project" "coded data" "original study"'; lead_classification=corpus_database_or_project_signal; score=11; reasons=strong_phrase:replication project | pair_term:original study | replication_word | original_word

4. review_id: review_figure1_search_leads_6c2f7ee495da
   lead_key: title:ecls_k_replication_project
   queue_status: needs_root_candidate_review
   name: ECLS-K Replication Project
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://osf.io/gvzwe/ | https://osf.io/hsgj2/
   source_key: gvzwe | hsgj2
   description: For ReScience X article
   current heuristic reason: Matched Figure 1 citation search query '"ReScience"'; lead_classification=corpus_database_or_project_signal; score=10; reasons=strong_phrase:replication project | replication_word | metadata_corpus_signal | query_phrase_in_text

5. review_id: review_figure1_search_leads_24788ac9a7b9
   lead_key: title:eleven_years_of_student_replication_projects_provide_evidence_on_the_correlates_of_replicability_in_psychology
   queue_status: needs_root_candidate_review
   name: Eleven years of student replication projects provide evidence on the correlates of replicability in psychology.
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1098/rsos.231240
   source_key: PMC10645069
   description: Cumulative scientific progress requires empirical results that are robust enough to support theory construction and extension. Yet in psychology, some prominent findings have failed to replicate, and large-scale studies suggest replicability issues are widespread. The identification of predictors of replication success is limited by the difficulty of conducting large samples of independent replication experiments, however: most investigations reanalyse the same set of 170 replications. We introduce a new dataset of 176 replications from students in a graduate-level methods course. Replication results were judged to be successful in 49% of replications; of the 136 where effect sizes could be numerically compared, 46% had point estimates within the prediction interval of the original outcome (versus the expected 95%). Larger original effect sizes and within-participants designs were especially related to replication success. Our results indicate that, consistent with prior reports, the robustness of the psychology literature is low enough to limit cumulative progress by student investigators.
   current heuristic reason: Matched Figure 1 bibliographic search query '"replication project" "coded data"'; lead_classification=corpus_database_or_project_signal; score=17; reasons=strong_phrase:replication project | pair_term:original effect | pair_term:effect size | data_term:data | data_term:dataset | replication_word | original_word | metadata_corpus_signal

6. review_id: review_figure1_search_leads_95434678b310
   lead_key: title:estimating_the_replicability_of_sports_and_exercise_science_research
   queue_status: needs_root_candidate_review
   name: Estimating the Replicability of Sports and Exercise Science Research.
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1007/s40279-025-02201-w
   source_key: PMC12513899 | https://openalex.org/W4411351188
   description: <h4>Background</h4>The replicability of sports and exercise research has not been assessed previously despite concerns about scientific practices within the field.<h4>Aim</h4>This study aims to provide an initial estimate of the replicability of applied sports and exercise science research published in quartile 1 journals (SCImago journal ranking for 2019 in the Sports Science subject category; www.scimagojr.com ) between 2016 and 2021.<h4>Methods</h4>A formalised selection protocol for this replication project was previously published. Voluntary collaborators were recruited, and studies were allocated in a stratified and randomised manner on the basis of equipment and expertise. Original authors were contacted to provide deidentified raw data, to review preregistrations and to provide methodological clarifications. A multiple inferential strategy was employed to analyse the replication data. The same analysis (i.e. F test or t test) was used to determine whether the replication effect size was statistically significant and in the same direction as the original effect size. Z-tests were used to determine whether the original and replication effect size estimates were compatible or significantly different in magnitude.<h4>Results</h4>In total, 25 replication studies were included for analysis. Of the 25, 10 replications used paired t tests, 1 used an independent t test and 14 used an analysis of variance (ANOVA) for the statistical analyses. In all, 7 (28%) studies demonstrated robust replicability, meeting all three validation criteria: achieving statistical significance (p
   current heuristic reason: Matched Figure 1 bibliographic search query '"replication project" "original study" "effect size"'; lead_classification=corpus_database_or_project_signal; score=25; reasons=strong_phrase:replication project | strong_phrase:replication studies | pair_term:original effect | pair_term:replication effect | pair_term:effect size | data_term:data | replication_word | original_word | effect_or_sample_size_phrase | metadata_corpus_signal

7. review_id: review_figure1_search_leads_12b18a2b607a
   lead_key: title:evaluating_meta_analysis_as_a_replication_success_measure
   queue_status: needs_root_candidate_review
   name: Evaluating meta-analysis as a replication success measure.
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1371/journal.pone.0308495
   source_key: PMC11633967
   description: <h4>Background</h4>The importance of replication in the social and behavioural sciences has been emphasized for decades. Various frequentist and Bayesian approaches have been proposed to qualify a replication study as successful or unsuccessful. One of them is meta-analysis. The focus of the present study is on the way meta-analysis functions as a replication success metric. To investigate this, original and replication studies that are part of two large-scale replication projects were used. For each original study, the probability of replication success was calculated using meta-analysis under different assumptions of the underlying population effect when replication results were unknown. The accuracy of the predicted overall replication success was evaluated once replication results became available using adjusted Brier scores.<h4>Results</h4>Our results showed that meta-analysis performed poorly when used as a replication success metric. In many cases, quantifying replication success using meta-analysis resulted in the conclusion where the replication was deemed a success regardless of the results of the replication study.<h4>Discussion</h4>We conclude that when using meta-analysis as a replication success metric, it has a relatively high probability of finding evidence in favour of a non-zero population effect even when it is zero. This behaviour largely results from the significance of the original study. Furthermore, we argue that there are fundamental reasons against using meta-analysis as a metric for replication success.
   current heuristic reason: Matched Figure 1 bibliographic search query '"replication success" "original study"'; lead_classification=corpus_database_or_project_signal; score=23; reasons=strong_phrase:replication project | strong_phrase:large-scale replication | strong_phrase:replication studies | pair_term:original study | replication_word | original_word | metadata_corpus_signal

8. review_id: review_figure1_search_leads_2822063673be
   lead_key: title:evidence_for_goal_and_mixed_evidence_for_false_belief_based_action_prediction_in_2_to_4_year_old_children_a_large_scale_
   queue_status: needs_root_candidate_review
   name: Evidence for goal‐ and mixed evidence for false belief‐based action prediction in 2‐ to 4‐year‐old children: A large‐scale longitudinal anticipatory looking replication study
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1111/desc.13224
   source_key: https://openalex.org/W4200361560
   description: Unsuccessful replication attempts of paradigms assessing children's implicit tracking of false beliefs have instigated the debate on whether or not children have an implicit understanding of false beliefs before the age of four. A novel multi-trial anticipatory looking false belief paradigm yielded evidence of implicit false belief reasoning in 3- to 4-year-old children using a combined score of two false belief conditions (Grosse Wiesmann, C., Friederici, A. D., Singer, T., & Steinbeis, N. [2017]. Developmental Science, 20(5), e12445). The present study is a large-scale replication attempt of this paradigm. The task was administered three times to the same sample of N = 185 children at 2, 3, and 4 years of age. Using the original stimuli, we did not replicate the original finding of above-chance belief-congruent looking in a combined score of two false belief conditions in either of the three age groups. Interestingly, the overall pattern of results was comparable to the original study. Post-hoc analyses revealed, however, that children performed above chance in one false belief condition (FB1) and below chance in the other false belief condition (FB2), thus yielding mixed evidence of children's false belief-based action predictions. Similar to the original study, participants' performance did not change with age and was not related to children's general language skills. This study demonstrates the importance of large-scaled replications and adds to the growing number of research questioning the validity and reliability of anticipatory looking false belief paradigms as a r
   current heuristic reason: Matched Figure 1 bibliographic search query '"large-scale replication" "original study"'; lead_classification=corpus_database_or_project_signal; score=13; reasons=strong_phrase:large-scale replication | pair_term:original study | replication_word | original_word | metadata_corpus_signal

9. review_id: review_figure1_search_leads_3c4dddb6790c
   lead_key: title:evidence_for_infant_directed_speech_preference_is_consistent_across_large_scale_multi_site_replication_and_meta_analysis
   queue_status: needs_root_candidate_review
   name: Evidence for Infant-directed Speech Preference Is Consistent Across Large-scale, Multi-site Replication and Meta-analysis.
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1162/opmi_a_00134
   source_key: PMC11045035
   description: There is substantial evidence that infants prefer infant-directed speech (IDS) to adult-directed speech (ADS). The strongest evidence for this claim has come from two large-scale investigations: i) a community-augmented meta-analysis of published behavioral studies and ii) a large-scale multi-lab replication study. In this paper, we aim to improve our understanding of the IDS preference and its boundary conditions by combining and comparing these two data sources across key population and design characteristics of the underlying studies. Our analyses reveal that both the meta-analysis and multi-lab replication show moderate effect sizes (<i>d</i> ≈ 0.35 for each estimate) and that both of these effects persist when relevant study-level moderators are added to the models (i.e., experimental methods, infant ages, and native languages). However, while the overall effect size estimates were similar, the two sources diverged in the effects of key moderators: both infant age and experimental method predicted IDS preference in the multi-lab replication study, but showed no effect in the meta-analysis. These results demonstrate that the IDS preference generalizes across a variety of experimental conditions and sampling characteristics, while simultaneously identifying key differences in the empirical picture offered by each source individually and pinpointing areas where substantial uncertainty remains about the influence of theoretically central moderators on IDS preference. Overall, our results show how meta-analyses and multi-lab replications can be used in tandem to understand
   current heuristic reason: Matched Figure 1 bibliographic search query '"multi-lab replication" "original study"'; lead_classification=corpus_database_or_project_signal; score=14; reasons=strong_phrase:multi-site replication | pair_term:effect size | data_term:data | replication_word | effect_or_sample_size_phrase | metadata_corpus_signal

10. review_id: review_figure1_search_leads_c7808e6c3826
   lead_key: title:examining_the_replicability_of_online_experiments_selected_by_a_decision_market
   queue_status: needs_root_candidate_review
   name: Examining the replicability of online experiments selected by a decision market.
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1038/s41562-024-02062-9
   source_key: PMC11860227
   description: Here we test the feasibility of using decision markets to select studies for replication and provide evidence about the replicability of online experiments. Social scientists (n = 162) traded on the outcome of close replications of 41 systematically selected MTurk social science experiments published in PNAS 2015-2018, knowing that the 12 studies with the lowest and the 12 with the highest final market prices would be selected for replication, along with 2 randomly selected studies. The replication rate, based on the statistical significance indicator, was 83% for the top-12 and 33% for the bottom-12 group. Overall, 54% of the studies were successfully replicated, with replication effect size estimates averaging 45% of the original effect size estimates. The replication rate varied between 54% and 62% for alternative replication indicators. The observed replicability of MTurk experiments is comparable to that of previous systematic replication projects involving laboratory experiments.
   current heuristic reason: Matched Figure 1 bibliographic search query '"replication project" "original study" "effect size"'; lead_classification=corpus_database_or_project_signal; score=19; reasons=strong_phrase:replication project | pair_term:original effect | pair_term:replication effect | pair_term:effect size | replication_word | original_word | effect_or_sample_size_phrase | metadata_corpus_signal

11. review_id: review_figure1_search_leads_17f20eab2f6e
   lead_key: title:experimental_economics_replication_project
   queue_status: needs_root_candidate_review
   name: Experimental Economics Replication Project
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://osf.io/bzm54/
   source_key: bzm54
   description: We replicate 18 laboratory experimental studies published in two high-impact economics journals in 2011-2014. All replications have a statistical power of ≥90% to detect the original effect size at the 5% significance level.
   current heuristic reason: Matched Figure 1 domain search query 'economics replication project data original study'; lead_classification=corpus_database_or_project_signal; score=17; reasons=strong_phrase:replication project | pair_term:original effect | pair_term:effect size | replication_word | original_word | effect_or_sample_size_phrase | metadata_corpus_signal

12. review_id: review_figure1_search_leads_04919281e4bd
   lead_key: title:fairsharing_record_for_framework_for_open_and_reproducible_research_training_replication_database
   queue_status: needs_root_candidate_review
   name: FAIRsharing record for: Framework for Open and Reproducible Research Training - Replication Database
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://fairsharing.org/10.25504/FAIRsharing.ee7dba
   source_key: 10.25504/fairsharing.ee7dba
   description: This FAIRsharing record describes: FORRT’s Replication Database (FReD) is a community-augmented, quantitative, meta-analytical interface of one of the most comprehensive collections of original and replication findings, including Replications and Reversals and large scale projects such as Many Labs or Registered Replication Reports. Via ReD, students, researchers, and applicants can create summaries of replication findings, search replications, investigate correlates of replicability, and automatically check for replications in reference lists.
   current heuristic reason: Matched Figure 1 repository search query '"replications and reversals" "database"'; lead_classification=corpus_database_or_project_signal; score=27; reasons=strong_phrase:replication database | strong_phrase:registered replication report | strong_phrase:many labs | strong_phrase:replications and reversals | data_term:data | data_term:database | replication_word | original_word | dataset_metadata_surface

13. review_id: review_figure1_search_leads_a5175f329fbc
   lead_key: title:fork_of_reproducibility_project_psychology
   queue_status: needs_root_candidate_review
   name: Fork of Reproducibility Project: Psychology
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://osf.io/wusvb/ | https://osf.io/eq3s2/
   source_key: wusvb | eq3s2
   description: Reproducibility is a defining feature of science, but the extent to which it characterizes current research is unknown. We conducted replications of 100 experimental and correlational studies published in three psychology journals using high-powered designs and original materials when available.
   current heuristic reason: Matched Figure 1 domain search query 'medicine reproducibility project replication dataset effect size'; lead_classification=corpus_database_or_project_signal; score=11; reasons=strong_phrase:reproducibility project | replication_word | original_word | metadata_corpus_signal

14. review_id: review_figure1_search_leads_404c6c8bc341
   lead_key: title:forrt_large_scale_replication_projects_hub
   queue_status: needs_root_candidate_review
   name: FORRT large-scale replication projects hub
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://forrt.org/replication-hub/large-scale-replication-projects/
   source_key: https://forrt.org/replication-hub/large-scale-replication-projects/
   description: Known source-family hub for large-scale replication projects and aliases that can seed Figure 1 corpus/database discovery. Page check: title=List of Large-Scale Replication Projects | FORRT - Framework for Open and Reproducible Research Training; html_bytes=29237; link_count=99
   current heuristic reason: Matched Figure 1 repository search query 'FORRT large-scale replication projects'; lead_classification=corpus_database_or_project_signal; score=15; reasons=strong_phrase:replication project | strong_phrase:large-scale replication | data_term:data | data_term:database | replication_word | query_phrase_in_text

15. review_id: review_figure1_search_leads_4c3314063449
   lead_key: title:forrt_replication_database
   queue_status: needs_root_candidate_review
   name: FORRT Replication Database
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://osf.io/9r62x/
   source_key: 9r62x
   description: Contains materials and data for the FORRT Replication Database
   current heuristic reason: Matched Figure 1 citation search query '"FReD" "Replication Database"'; lead_classification=corpus_database_or_project_signal; score=12; reasons=strong_phrase:replication database | data_term:data | data_term:database | replication_word | repository_data_surface | metadata_corpus_signal

16. review_id: review_figure1_search_leads_fa29ed98a4b6
   lead_key: title:forrt_replication_database_frozen_version_from_08_2024
   queue_status: needs_root_candidate_review
   name: FORRT Replication Database (frozen version from 08/2024)
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://osf.io/c9rny/
   source_key: c9rny
   description: Contains materials and data for the FORRT Replication Database
   current heuristic reason: Matched Figure 1 citation search query '"FReD" "Replication Database"'; lead_classification=corpus_database_or_project_signal; score=12; reasons=strong_phrase:replication database | data_term:data | data_term:database | replication_word | repository_data_surface | metadata_corpus_signal

17. review_id: review_figure1_search_leads_9fabfd38878d
   lead_key: title:forrt_replication_database_fred
   queue_status: needs_root_candidate_review
   name: FORRT Replication Database / FReD
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: reports/corpus_suggestion_tracker.md
   source_key: manual_tracker_row_forrt_replication_database_fred_190c922e4730
   description: Manual suggestion tracker row; status=worked; parser caveats; row=2 | FORRT Replication Database / FReD | worked; parser caveats | Parser now yields 1,969 original-claim rows across 762 original-paper DOI units. Paper-level slope `-0.421`; p<.10 share about 94%. | Not a random journal-paper sample. Rows are original findings selected into replication projects/databases or submitted as replications, so this is a replication-target/focal-claim frame. Not all rows are treatment/intervention effects.
   current heuristic reason: Matched Figure 1 manual search query 'user-suggested replication datasets'; lead_classification=corpus_database_or_project_signal; score=18; reasons=strong_phrase:replication database | strong_phrase:replication project | data_term:data | data_term:database | replication_word | original_word | manual_tracker_status_signal

18. review_id: review_figure1_search_leads_e4909bfbc5b5
   lead_key: title:growth_from_uncertainty_understanding_the_replication_crisis_in_infant_cognition
   queue_status: needs_root_candidate_review
   name: Growth From Uncertainty: Understanding the Replication ‘Crisis’ in Infant Cognition
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1017/psa.2023.157
   source_key: https://openalex.org/W4388716787
   description: Abstract Psychology is a discipline that has a high number of failed replications, which has been characterized as a “crisis” on the assumption that failed replications are indicative of untrustworthy research. This article uses Chang’s concept of epistemic iteration to show how a research program can advance epistemic goals despite many failed replications. It illustrates this by analyzing an ongoing large-scale replication attempt of Southgate et al.’s work exploring infants’ understanding of false beliefs. It concludes that epistemic iteration offers a way of understanding the value of replications—both failed and successful—that contradicts the narrative centered around distrust.
   current heuristic reason: Matched Figure 1 citation search query '"ManyBabies" "replication data"'; lead_classification=corpus_database_or_project_signal; score=9; reasons=strong_phrase:large-scale replication | replication_word | metadata_corpus_signal

19. review_id: review_figure1_search_leads_4267dbece1dc
   lead_key: title:hack_setting_up_a_large_scale_replication_project_of_cognitive_dissonance_theory_beatrix_zone_4_14_45
   queue_status: needs_root_candidate_review
   name: Hack - Setting Up A Large Scale Replication Project of Cognitive Dissonance Theory (Beatrix Zone 4; 14:45)
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://osf.io/294bx/
   source_key: 294bx
   description: 
   current heuristic reason: Matched Figure 1 repository search query '"large-scale replication project" "original study"'; lead_classification=corpus_database_or_project_signal; score=7; reasons=strong_phrase:replication project | replication_word

20. review_id: review_figure1_search_leads_91f39c20a32f
   lead_key: title:heterogeneity_in_direct_replications_in_psychology_and_its_association_with_effect_size
   queue_status: needs_root_candidate_review
   name: Heterogeneity in direct replications in psychology and its association with effect size.
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1037/bul0000294 | https://osf.io/rs7dm/ | https://osf.io/4z3e7/
   source_key: https://openalex.org/W3044062510 | rs7dm | 4z3e7 | 10.1037/bul0000294
   description: We examined the evidence for heterogeneity (of effect sizes) when only minor changes to sample population and settings were made between studies and explored the association between heterogeneity and average effect size in a sample of 68 meta-analyses from 13 preregistered multilab direct replication projects in social and cognitive psychology. Among the many examined effects, examples include the Stroop effect, the "verbal overshadowing" effect, and various priming effects such as "anchoring" effects. We found limited heterogeneity; 48/68 (71%) meta-analyses had nonsignificant heterogeneity, and most (49/68; 72%) were most likely to have zero to small heterogeneity. Power to detect small heterogeneity (as defined by Higgins, Thompson, Deeks, & Altman, 2003) was low for all projects (mean 43%), but good to excellent for medium and large heterogeneity. Our findings thus show little evidence of widespread heterogeneity in direct replication studies in social and cognitive psychology, suggesting that minor changes in sample population and settings are unlikely to affect research outcomes in these fields of psychology. We also found strong correlations between observed average effect sizes (standardized mean differences and log odds ratios) and heterogeneity in our sample. Our results suggest that heterogeneity and moderation of effects is unlikely for a 0 average true effect size, but increasingly likely for larger average true effect size. (PsycInfo Database Record (c) 2020 APA, all rights reserved).
   current heuristic reason: Matched Figure 1 domain search query 'psychology replication database effect size'; lead_classification=corpus_database_or_project_signal; score=20; reasons=strong_phrase:replication project | strong_phrase:replication studies | pair_term:effect size | data_term:data | data_term:database | replication_word | effect_or_sample_size_phrase | metadata_corpus_signal

21. review_id: review_figure1_search_leads_7e275ed173e3
   lead_key: title:how_replicable_are_links_between_personality_traits_and_consequential_life_outcomes_the_life_outcomes_of_personality_rep
   queue_status: needs_root_candidate_review
   name: How Replicable Are Links Between Personality Traits and Consequential Life Outcomes? The Life Outcomes of Personality Replication Project
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1177/0956797619831612
   source_key: https://openalex.org/W2884318343
   description: The Big Five personality traits have been linked to dozens of life outcomes. However, metascientific research has raised questions about the replicability of behavioral science. The Life Outcomes of Personality Replication (LOOPR) Project was therefore conducted to estimate the replicability of the personality-outcome literature. Specifically, I conducted preregistered, high-powered (median N = 1,504) replications of 78 previously published trait-outcome associations. Overall, 87% of the replication attempts were statistically significant in the expected direction. The replication effects were typically 77% as strong as the corresponding original effects, which represents a significant decline in effect size. The replicability of individual effects was predicted by the effect size and design of the original study, as well as the sample size and statistical power of the replication. These results indicate that the personality-outcome literature provides a reasonably accurate map of trait-outcome associations but also that it stands to benefit from efforts to improve replicability.
   current heuristic reason: Matched Figure 1 citation search query '"LOOPR" "replication"'; lead_classification=corpus_database_or_project_signal; score=23; reasons=strong_phrase:replication project | pair_term:original study | pair_term:original effect | pair_term:replication effect | pair_term:effect size | pair_term:sample size | replication_word | original_word | effect_or_sample_size_phrase | metadata_corpus_signal

22. review_id: review_figure1_search_leads_9d2732b5c6ab
   lead_key: title:improving_statistical_analysis_in_team_science_the_case_of_a_bayesian_multiverse_of_many_labs_4
   queue_status: needs_root_candidate_review
   name: Improving Statistical Analysis in Team Science: The Case of a Bayesian Multiverse of Many Labs 4
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.31234/osf.io/cb9er
   source_key: https://openalex.org/W3163808281
   description: Team science projects have become the gold standard for assessing the replicability and variability of key findings in psychological science. However, we believe the typical meta-analytic approach in these projects fails to match the wealth of collected data. Instead, we advocate the use of Bayesian hierarchical modeling for team science projects, potentially extended in a multiverse analysis. We illustrate this full-scale analysis by applying it to the recently published Many Labs 4 project. This project aimed to replicate the mortality salience effect – that being reminded of one’s own death strengthens the own cultural identity. In a multiverse analysis we assess the robustness of the results with varying data inclusion criteria and prior settings. Bayesian model comparison results largely converge to a common conclusion: the data provide evidence against a mortality salience effect across the majority of our analyses. We issue general recommendations to facilitate full-scale analyses in team science projects.
   current heuristic reason: Matched Figure 1 citation search query '"Many Labs" "original study" -> cites:W3163230172'; lead_classification=corpus_database_or_project_signal; score=7; reasons=strong_phrase:many labs | pair_term:full-scale | data_term:data | metadata_corpus_signal | no_replication_language_penalty

23. review_id: review_figure1_search_leads_0cc39d545ae2
   lead_key: title:incidental_attitude_formation_via_the_surveillance_task_a_multi_site_registered_replication_report_of_olson_and_fazio_20
   queue_status: needs_root_candidate_review
   name: Incidental Attitude Formation via the Surveillance Task: A Multi-Site Registered Replication Report of Olson and Fazio (2001) "Implicit Attitude Formation Through Classical Conditioning"
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://osf.io/xqv8b/
   source_key: xqv8b
   description: Measures, researcher instructions, data processing, analysis, and meta-analysis for a Registered Replication Report of Olson &amp; Fazio (2001) to examine the evidence for evaluative conditioning outside of awareness/recollective memory. NB nomenclature has changed over time: despite the title of the original article, "implicit" here refers to self-reported attitudes that were acquired in the absence of awareness/memory of the CS-US pairings, rather than classical conditioning procedures giving rise to implicit attitudes.
   current heuristic reason: Matched Figure 1 repository search query '"registered replication report" data'; lead_classification=corpus_database_or_project_signal; score=11; reasons=strong_phrase:registered replication report | data_term:data | replication_word | original_word | repository_data_surface

24. review_id: review_figure1_search_leads_28438c56840e
   lead_key: title:incorrect_data_in_tables_in_nonvalidation_of_reported_genetic_risk_factors_for_acute_coronary_syndrome_in_a_large_scale_
   queue_status: needs_root_candidate_review
   name: Incorrect Data in Tables in: Nonvalidation of Reported Genetic Risk Factors for Acute Coronary Syndrome in a Large-Scale Replication Study
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1001/jama.298.9.973-b
   source_key: 10.1001/jama.298.9.973-b
   description: 
   current heuristic reason: Matched Figure 1 bibliographic search query '"large-scale replication" "original study"'; lead_classification=corpus_database_or_project_signal; score=10; reasons=strong_phrase:large-scale replication | data_term:data | replication_word | metadata_corpus_signal

25. review_id: review_figure1_search_leads_12655154c792
   lead_key: title:information_bottlenecks_in_behavioural_science_a_framework_and_multi_dataset_analysis_of_replication_and_generalization
   queue_status: needs_root_candidate_review
   name: Information bottlenecks in Behavioural Science: A framework and multi-dataset analysis of replication and generalization
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://osf.io/n67tk/
   source_key: n67tk
   description: The replication crisis has revealed systematic weaknesses in the transmission of scientific knowledge. Here we introduce an information-theoretic framework to quantify how much variability in the world is captured by experiments, retained across replications, and transmitted to a downstream community judgment, operationalized here by direct replication outcomes. We define three measures—Capture, Retention, and Generalizability—based on mutual information between world-level effect sizes, original significance outcomes, and replication outcomes. We apply this approach to four data sets from known replication projects. Results show that only a small fraction of variability in effect sizes is captured by significance testing, and even less is retained in replication. This perspective highlights science as an information-processing system, providing a quantitative account of why the scientific pipeline is so lossy.
   current heuristic reason: Matched Figure 1 domain search query 'management science replication project dataset'; lead_classification=corpus_database_or_project_signal; score=16; reasons=strong_phrase:replication project | pair_term:effect size | data_term:data | data_term:dataset | replication_word | original_word | repository_data_surface | metadata_corpus_signal

26. review_id: review_figure1_search_leads_aa2a7bf31db3
   lead_key: title:investigating_the_replicability_of_preclinical_cancer_biology
   queue_status: needs_root_candidate_review
   name: Investigating the replicability of preclinical cancer biology.
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.7554/elife.71601
   source_key: PMC8651293 | https://openalex.org/W4200247206
   description: Replicability is an important feature of scientific research, but aspects of contemporary research culture, such as an emphasis on novelty, can make replicability seem less important than it should be. The Reproducibility Project: Cancer Biology was set up to provide evidence about the replicability of preclinical research in cancer biology by repeating selected experiments from high-impact papers. A total of 50 experiments from 23 papers were repeated, generating data about the replicability of a total of 158 effects. Most of the original effects were positive effects (136), with the rest being null effects (22). A majority of the original effect sizes were reported as numerical values (117), with the rest being reported as representative images (41). We employed seven methods to assess replicability, and some of these methods were not suitable for all the effects in our sample. One method compared effect sizes: for positive effects, the median effect size in the replications was 85% smaller than the median effect size in the original experiments, and 92% of replication effect sizes were smaller than the original. The other methods were binary - the replication was either a success or a failure - and five of these methods could be used to assess both positive and null effects when effect sizes were reported as numerical values. For positive effects, 40% of replications (39/97) succeeded according to three or more of these five methods, and for null effects 80% of replications (12/15) were successful on this basis; combining positive and null effects, the success rate was 4
   current heuristic reason: Matched Figure 1 bibliographic search query '"replication rates" "coded" "effect sizes"'; lead_classification=corpus_database_or_project_signal; score=20; reasons=strong_phrase:reproducibility project | pair_term:original effect | pair_term:replication effect | pair_term:effect size | data_term:data | replication_word | original_word | effect_or_sample_size_phrase | metadata_corpus_signal

27. review_id: review_figure1_search_leads_564cac4ef29e
   lead_key: title:investigating_variation_in_replicability_a_many_labs_replication_project
   queue_status: needs_root_candidate_review
   name: Investigating Variation in Replicability: A “Many Labs” Replication Project
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1027/1864-9335/a000178 | https://osf.io/scayl/ | https://osf.io/wx7ck/
   source_key: 10.1027/1864-9335/a000178 | scayl | wx7ck
   description: Semantic Scholar reference neighbor for known corpus/source-family DOI 10.1038/s41562-016-0021.
   current heuristic reason: Matched Figure 1 link_graph search query '10.1038/s41562-016-0021'; lead_classification=corpus_database_or_project_signal; score=17; reasons=strong_phrase:replication project | strong_phrase:many labs | replication_word | known_corpus_paper_link_graph | query_phrase_in_text

28. review_id: review_figure1_search_leads_5cfa0a0e552f
   lead_key: title:linguistic_compression_predicts_replication_failure
   queue_status: needs_root_candidate_review
   name: Linguistic Compression Predicts Replication Failure
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.17605/osf.io/cpe6f
   source_key: https://openalex.org/W7148330249
   description: This study tests whether linguistic compression in scientific methods sections predicts replication failure. Specifically, it tests whether low temporal conditionality (T-Low: procedures stated without parametric bounds or conditional qualifiers) and low semantic specificity (Sp-Low: categorical rather than parametric descriptions) are higher in papers that failed to replicate than in papers that successfully replicated. The prediction derives from the Conscious Force theoretical framework (Prediction 49): compressed language in methods sections reflects genuine procedural ambiguity — the researcher degrees of freedom that produce non-replicable findings. High-fidelity methods language (specific, conditionally bounded, parametric) reflects procedures specified precisely enough to reproduce. Data source: OSF Reproducibility Project (100 papers), Many Labs 1-3, and the Social Sciences Replication Project (21 papers). Expected N = 150-200 papers with known replication outcomes. All data publicly available. No new data collection required. Design: Archival, single-coder, exploratory pre-registration. Coding has not begun. Replication outcomes are stored separately and will not be merged with coded data until coding is complete.
   current heuristic reason: Matched Figure 1 bibliographic search query '"replication project" "coded data"'; lead_classification=corpus_database_or_project_signal; score=22; reasons=strong_phrase:replication project | strong_phrase:reproducibility project | strong_phrase:many labs | data_term:data | data_term:code | data_term:osf | replication_word | metadata_corpus_signal

29. review_id: review_figure1_search_leads_6e8201e677b6
   lead_key: title:ljcolling_attentional_snarc_v1_0
   queue_status: needs_root_candidate_review
   name: ljcolling/attentional_snarc V1.0
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://zenodo.org/records/3738555
   source_key: 3738555
   description: Repository for Registered Replication Report on Fischer, Castel, Dodd, and Pratt (2003)
   current heuristic reason: Matched Figure 1 repository search query '"registered replication report" "data"'; lead_classification=corpus_database_or_project_signal; score=8; reasons=strong_phrase:registered replication report | data_term:repository | replication_word

30. review_id: review_figure1_search_leads_259d97d285f9
   lead_key: title:management_science_reproducibility_project
   queue_status: needs_root_candidate_review
   name: Management Science Reproducibility Project
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://osf.io/mjqg5/
   source_key: mjqg5
   description: In the Management Science Reproducibility Project (ManSciReP) we aim to assess the computational reproducibility of studies published in the journal. All papers submitted after June 1, 2019 are subject to code and data review according to the journal’s 2019 Data and Code Disclosure Policy. In this project, we will create a large sample of papers from both before and after the 2019 Data and Code Disclosure Policy took effect. We recruit reviewers (from the Management Science community and outside) who are assigned an article from their own research field, and asked to attempt to reproduce the main results reported in that article. Through a structured survey, reviewers then report back on the extent to which they were able to reproduce the tables, figures, and other main results in the manuscript, and what obstacles they experienced in this endeavor.
   current heuristic reason: Matched Figure 1 domain search query 'management science replication project dataset'; lead_classification=corpus_database_or_project_signal; score=10; reasons=strong_phrase:reproducibility project | data_term:data | data_term:code | repository_data_surface | metadata_corpus_signal

31. review_id: review_figure1_search_leads_7e7ef2f792a4
   lead_key: title:many_labs_2_through_bear
   queue_status: needs_root_candidate_review
   name: Many Labs 2 through BEAR
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: reports/corpus_suggestion_tracker.md
   source_key: manual_tracker_row_many_labs_2_through_bear_7b25d68b1bb5
   description: Manual suggestion tracker row; status=working comparator; row=Many Labs 2 through BEAR | working comparator | Audited as replication sanity check. | Median `D ~= 0.147`, median `N = 93`. | Good realistic-effects comparator, not original published literature.
   current heuristic reason: Matched Figure 1 manual search query 'user-suggested replication datasets'; lead_classification=corpus_database_or_project_signal; score=9; reasons=strong_phrase:many labs | replication_word | original_word

32. review_id: review_figure1_search_leads_3e8f2b6a7821
   lead_key: title:many_labs_2_investigating_variation_in_replicability_across_samples_and_settings
   queue_status: needs_root_candidate_review
   name: Many Labs 2: Investigating Variation in Replicability Across Samples and Settings
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1177/2515245918810225
   source_key: https://openalex.org/W2776961836 | 10.1177/2515245918810225
   description: We conducted preregistered replications of 28 classic and contemporary published findings, with protocols that were peer reviewed in advance, to examine variation in effect magnitudes across samples and settings. Each protocol was administered to approximately half of 125 samples that comprised 15,305 participants from 36 countries and territories. Using the conventional criterion of statistical significance ( p &lt; .05), we found that 15 (54%) of the replications provided evidence of a statistically significant effect in the same direction as the original finding. With a strict significance criterion ( p &lt; .0001), 14 (50%) of the replications still provided such evidence, a reflection of the extremely high-powered design. Seven (25%) of the replications yielded effect sizes larger than the original ones, and 21 (75%) yielded effect sizes smaller than the original ones. The median comparable Cohen’s ds were 0.60 for the original findings and 0.15 for the replications. The effect sizes were small (&lt; 0.20) in 16 of the replications (57%), and 9 effects (32%) were in the direction opposite the direction of the original effect. Across settings, the Q statistic indicated significant heterogeneity in 11 (39%) of the replication effects, and most of those were among the findings with the largest overall effect sizes; only 1 effect that was near zero in the aggregate showed significant heterogeneity according to this measure. Only 1 effect had a tau value greater than .20, an indication of moderate heterogeneity. Eight others had tau values near or slightly above .10, an ind
   current heuristic reason: Matched Figure 1 domain search query '"many-lab" dataset original'; lead_classification=corpus_database_or_project_signal; score=17; reasons=strong_phrase:many labs | pair_term:original effect | pair_term:replication effect | pair_term:effect size | pair_term:cohen | replication_word | original_word

33. review_id: review_figure1_search_leads_260d50672dd4
   lead_key: title:many_labs_3_manuscript_tables
   queue_status: needs_root_candidate_review
   name: Many Labs 3 Manuscript Tables
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: data/raw/replication_projects/ml3/Many Labs 3 Manuscript Tables.txt
   source_key: data/raw/replication_projects/ml3/Many Labs 3 Manuscript Tables.txt
   description: Local scan hit; file_type=text_or_code; matched_query=study_pair_id original replication; path=data/raw/replication_projects/ml3/Many Labs 3 Manuscript Tables.txt; snippet=52 Table 3 Original and replication results Null Hypothesis Significance
   current heuristic reason: Matched Figure 1 code search query 'study_pair_id original replication'; lead_classification=corpus_database_or_project_signal; score=15; reasons=strong_phrase:many labs | data_term:data | data_term:code | replication_word | original_word | local_table_or_code_surface | query_phrase_in_text

34. review_id: review_figure1_search_leads_c0918685ac7b
   lead_key: title:many_labs_3_elm_follow_up_study
   queue_status: needs_root_candidate_review
   name: Many Labs 3: ELM Follow Up Study
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://osf.io/chxja/
   source_key: chxja
   description: Luttrell and colleagues (2016) followed up on one of the replications conducted as a part of Many Labs 3 (Cacioppo, Petty, &amp; Morris, 1983), correcting what they identified as weaknesses to the Many Labs 3 version. They found the original effect in their optimal version but not in the Many Labs 3 version. In this study, we seek to replicate their methodology, demonstrating that expertise can be transferred between teams when conducting replications.
   current heuristic reason: Matched Figure 1 citation search query '"Many Labs 3" replication data'; lead_classification=corpus_database_or_project_signal; score=11; reasons=strong_phrase:many labs | pair_term:original effect | replication_word | original_word

35. review_id: review_figure1_search_leads_01329bffde9f
   lead_key: title:many_labs_4_replicating_mortality_salience_with_and_without_original_author_involvement
   queue_status: needs_root_candidate_review
   name: Many Labs 4: Replicating Mortality Salience with and without Original Author Involvement
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://osf.io/8ccnw/
   source_key: 8ccnw
   description: We conduct replications of the same TMT study across 17 labs, half with detailed advice from original authors, half without any help whatsoever.
   current heuristic reason: Matched Figure 1 repository search query '"original" "replication" "Cohen" "N"'; lead_classification=corpus_database_or_project_signal; score=9; reasons=strong_phrase:many labs | replication_word | original_word

36. review_id: review_figure1_search_leads_d5a9d9866eb6
   lead_key: title:many_labs_5_registered_multisite_replication_of_the_tempting_fate_effects_in_risen_and_gilovich_2008
   queue_status: needs_root_candidate_review
   name: Many Labs 5: Registered Multisite Replication of the Tempting-Fate Effects in Risen and Gilovich (2008)
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1177/2515245918785165
   source_key: https://openalex.org/W3102574417
   description: Risen and Gilovich (2008) found that subjects believed that “tempting fate” would be punished with ironic bad outcomes (a main effect), and that this effect was magnified when subjects were under cognitive load (an interaction). A previous replication study (Frank &amp; Mathur, 2016) that used an online implementation of the protocol on Amazon Mechanical Turk failed to replicate both the main effect and the interaction. Before this replication was run, the authors of the original study expressed concern that the cognitive-load manipulation may be less effective when implemented online than when implemented in the lab and that subjects recruited online may also respond differently to the specific experimental scenario chosen for the replication. A later, large replication project, Many Labs 2 (Klein et al. 2018), replicated the main effect (though the effect size was smaller than in the original study), but the interaction was not assessed. Attempting to replicate the interaction while addressing the original authors’ concerns regarding the protocol for the first replication study, we developed a new protocol in collaboration with the original authors. We used four university sites ( N = 754) chosen for similarity to the site of the original study to conduct a high-powered, preregistered replication focused primarily on the interaction effect. Results from these sites did not support the interaction or the main effect and were comparable to results obtained at six additional universities that were less similar to the original site. Post hoc analyses did not provide strong ev
   current heuristic reason: Matched Figure 1 citation search query '"Many Labs" "original study"'; lead_classification=corpus_database_or_project_signal; score=22; reasons=strong_phrase:replication project | strong_phrase:many labs | pair_term:original study | pair_term:effect size | replication_word | original_word | effect_or_sample_size_phrase | metadata_corpus_signal

37. review_id: review_figure1_search_leads_6799979ce111
   lead_key: title:many_labs_5_registered_replication_of_lobue_and_deloache_2008
   queue_status: needs_root_candidate_review
   name: Many Labs 5: Registered Replication of LoBue and DeLoache (2008)
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1177/2515245920953350
   source_key: 10.1177/2515245920953350
   description: <jats:p>Across three studies, LoBue and DeLoache (2008) provided evidence suggesting that both young children and adults exhibit enhanced visual detection of evolutionarily relevant threat stimuli (as compared with nonthreatening stimuli). A replication of their Experiment 3, conducted by Cramblet Alvarez and Pipitone (2015) as part of the Reproducibility Project: Psychology (RP:P), demonstrated trends similar to those of the original study, but the effect sizes were smaller and not statistically significant. There were, however, some methodological differences (e.g., screen size) and sampling differences (the age of recruited children) between the original study and the RP:P replication study. Additionally, LoBue and DeLoache expressed concern over the choice of stimuli used in the RP:P replication. We sought to explore the possible moderating effects of these factors by conducting two new replications—one using the protocol from the RP:P and the other using a revised protocol. We collected data at four sites, three in Serbia and one in the United States (total N = 553). Overall, participants were not significantly faster at detecting threatening stimuli. Thus, results were not supportive of the hypothesis that visual detection of evolutionarily relevant threat stimuli is enhanced in young children. The effect from the RP:P protocol ( d = −0.10, 95% confidence interval = [−1.02, 0.82]) was similar to the effect from the revised protocol ( d = −0.09, 95% confidence interval =
   current heuristic reason: Matched Figure 1 citation search query '"registered replication report" "many labs"'; lead_classification=corpus_database_or_project_signal; score=21; reasons=strong_phrase:reproducibility project | strong_phrase:many labs | pair_term:original study | pair_term:effect size | data_term:data | replication_word | original_word | metadata_corpus_signal

38. review_id: review_figure1_search_leads_ae6a07debb0a
   lead_key: title:many_labs_5_testing_pre_data_collection_peer_review_as_an_intervention_to_increase_replicability
   queue_status: needs_root_candidate_review
   name: Many Labs 5: Testing Pre-Data-Collection Peer Review as an Intervention to Increase Replicability
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1177/2515245920958687 | https://doi.org/10.31234/osf.io/sxfm2 | https://osf.io/7a6rd/
   source_key: https://openalex.org/W2936257342 | 10.1177/2515245920958687 | https://openalex.org/W4241961269 | 7a6rd
   description: Replication studies in psychological science sometimes fail to reproduce prior findings. If these studies use methods that are unfaithful to the original study or ineffective in eliciting the phenomenon of interest, then a failure to replicate may be a failure of the protocol rather than a challenge to the original finding. Formal pre-data-collection peer review by experts may address shortcomings and increase replicability rates. We selected 10 replication studies from the Reproducibility Project: Psychology (RP:P; Open Science Collaboration, 2015) for which the original authors had expressed concerns about the replication designs before data collection; only one of these studies had yielded a statistically significant effect ( p &lt; .05). Commenters suggested that lack of adherence to expert review and low-powered tests were the reasons that most of these RP:P studies failed to replicate the original effects. We revised the replication protocols and received formal peer review prior to conducting new replication studies. We administered the RP:P and revised protocols in multiple laboratories (median number of laboratories per original study = 6.5, range = 3–9; median total sample = 1,279.5, range = 276–3,512) for high-powered tests of each original finding with both protocols. Overall, following the preregistered analysis plan, we found that the revised protocols produced effect sizes similar to those of the RP:P protocols (Δ r = .002 or .014, depending on analytic approach). The median effect size for the revised protocols ( r = .05) was similar to that of the RP:P prot
   current heuristic reason: Matched Figure 1 bibliographic search query '"reproducibility project" "effect sizes"'; lead_classification=corpus_database_or_project_signal; score=30; reasons=strong_phrase:reproducibility project | strong_phrase:many labs | strong_phrase:replication studies | pair_term:original study | pair_term:original effect | pair_term:effect size | data_term:data | replication_word | original_word | effect_or_sample_size_phrase | metadata_corpus_signal

39. review_id: review_figure1_search_leads_8485305810cb
   lead_key: title:mastroianni_2023_replication_project
   queue_status: needs_root_candidate_review
   name: Mastroianni_2023 Replication Project
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://osf.io/bt58q/
   source_key: bt58q
   description: Psych 251 Replication project -- Fall 2025. This is a pre-data collection registration of "The Illusion of Moral Decline" by Adam Mastroianni (2023), described fully in "mastroianni2023_report.qmd." All planned analyses and exclusions are reported. The planned sample size is 100 and the rationale and calculations for this sample size are given in the report. Specifically, this is a replication of part 2c of the original study. The purpose is to establish a connection between perceived morality of the current year, the year the participant turned 20, and the year the participant was born. In the literature, there is already an established effect of humans perceiving the occurrence of moral decline, the idea that people are less kind, honest, nice, and good than they were previously. Mastroianni found a significant effect size in study 2c in multiple comparisons of the aforementioned timeframes, the same outcome is expected in this replication. The format of this study has respondents from Prolific answer a Qualtrics study with a series of questions about their perceived morality at certain times.
   current heuristic reason: Matched Figure 1 repository search query '"replication project" "coded data" "original study"'; lead_classification=corpus_database_or_project_signal; score=19; reasons=strong_phrase:replication project | pair_term:original study | pair_term:effect size | pair_term:sample size | data_term:data | replication_word | original_word | effect_or_sample_size_phrase | repository_data_surface

40. review_id: review_figure1_search_leads_70e5d8b15172
   lead_key: title:meta_analysis
   queue_status: needs_root_candidate_review
   name: Meta-Analysis
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.4324/9781351137713-22
   source_key: https://openalex.org/W4235752323
   description: This chapter focuses on the ubiquity and extent of heterogeneity in behavioral research. It reviews three classes of meta-analytic techniques. The chapter also reviews meta-analytic techniques that assess and adjust for publication bias. It discusses how meta-analytic techniques can accommodate study-level covariates. The Many Labs and registered replication reports approach allows data to be integrated via meta-analysis—with the data from each laboratory treated as an independent replication study—to provide an assessment of heterogeneity. There are a number of meta-analytic techniques based on standardized effect sizes on standardized scales such as the J. Cohen’s d scale and the correlation scale. The chapter discusses two techniques—so-called single paper meta-analysis and multilevel multivariate meta-analysis—based on basic summary information such as means, standard deviations, and sample sizes. It is often of interest in meta-analysis to assess the relationship between the effect of interest and one or more study-level covariates.
   current heuristic reason: Matched Figure 1 citation search query '"registered replication report" "many labs"'; lead_classification=corpus_database_or_project_signal; score=19; reasons=strong_phrase:registered replication report | strong_phrase:many labs | pair_term:effect size | pair_term:sample size | pair_term:cohen | data_term:data | replication_word

41. review_id: review_figure1_search_leads_1a3d8a55761a
   lead_key: title:meta_analyzing_the_multiverse_a_peek_under_the_hood_of_selective_reporting
   queue_status: needs_root_candidate_review
   name: Meta-analyzing the multiverse: A peek under the hood of selective reporting.
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1037/met0000559
   source_key: https://openalex.org/W4376130954
   description: -hacking) from this "multiverse" of outcomes can inflate effect size estimates and false positive rates. We studied the effects of researcher degrees of freedom and selective reporting using empirical data from extensive multistudy projects in psychology (Registered Replication Reports) featuring 211 samples and 14 dependent variables. We used a counterfactual design to examine what biases could have emerged if the studies (and ensuing meta-analyses) had not been preregistered and could have been subjected to selective reporting based on the significance of the outcomes in the primary studies. Our results show the substantial variability in effect sizes that researcher degrees of freedom can create in relatively standard psychological studies, and how selective reporting of outcomes can alter conclusions and introduce bias in meta-analysis. Despite the typically thousands of outcomes appearing in the multiverses of the 294 included studies, only in about 30% of studies did significant effect sizes in the hypothesized direction emerge. We also observed that the effect of a particular researcher degree of freedom was inconsistent across replication studies using the same protocol, meaning multiverse analyses often fail to replicate across samples. We recommend hypothesis-testing researchers to preregister their preferred analysis and openly report multiverse analysis. We propose a descriptive index (underlying multiverse variability) that quantifies the robustness of results across alternative ways to analyze the data. (PsycInfo Database Record (c) 2025 APA, all rights reserv
   current heuristic reason: Matched Figure 1 citation search query '"registered replication report" "many labs" -> cites:W4210766447'; lead_classification=corpus_database_or_project_signal; score=20; reasons=strong_phrase:registered replication report | strong_phrase:replication studies | pair_term:effect size | data_term:data | data_term:database | replication_word | effect_or_sample_size_phrase | metadata_corpus_signal

42. review_id: review_figure1_search_leads_88df5047a765
   lead_key: title:meta_regression_to_explain_shrinkage_and_heterogeneity_in_large_scale_replication_projects
   queue_status: needs_root_candidate_review
   name: Meta-regression to explain shrinkage and heterogeneity in large-scale replication projects.
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1371/journal.pone.0327799 | https://doi.org/10.31222/osf.io/e9nw2_v3 | https://zenodo.org/records/15552808
   source_key: PMC12316214 | https://doi.org/10.31222/osf.io/e9nw2_v3 | 15552808
   description: Recent large-scale replication projects (RPs) have estimated concerningly low reproducibility rates. Further, they reported substantial degrees of shrinkage of effect size, where the replication effect size was found to be, on average, much smaller than the original effect size. Within these RPs, the included original-replication study-pairs can vary with respect to aspects of study design, outcome measures, and descriptive features of both original and replication study population and study team. This often results in between-study-pair heterogeneity, i.e., variation in effect size differences across study-pairs that goes beyond expected statistical variation. When broader claims about the reproducibility of an entire field are based on such heterogeneous data, it becomes imperative to conduct a rigorous analysis of the amount and sources of shrinkage and heterogeneity within and between included study-pairs. Methodology from the meta-analysis literature provides an approach for quantifying the heterogeneity present in RPs with an additive or multiplicative parameter. Meta-regression methodology further allows for an investigation into the sources of shrinkage and heterogeneity. We propose the use of location-scale meta-regressions as a means to directly relate the identified characteristics with shrinkage (represented by the location) and heterogeneity (represented by the scale). This provides valuable insights into drivers and factors associated with high or low reproducibility rates and therefore contextualises results of RPs. The proposed methodology is illustrated usi
   current heuristic reason: Matched Figure 1 domain search query '"many-lab" dataset original'; lead_classification=corpus_database_or_project_signal; score=25; reasons=strong_phrase:replication project | strong_phrase:large-scale replication | pair_term:original effect | pair_term:replication effect | pair_term:effect size | data_term:data | replication_word | original_word | effect_or_sample_size_phrase | metadata_corpus_signal

43. review_id: review_figure1_search_leads_2c271775d893
   lead_key: title:metascientific_replication_project_with_the_advanced_meta_experimental_protocol_of_the_transparent_psi_project_procedure
   queue_status: needs_root_candidate_review
   name: Metascientific replication project with the advanced meta-experimental protocol of the transparent psi project procedures for testing the precognitive effect claimed by Bem.
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1371/journal.pone.0335330
   source_key: PMC12588471
   description: This metascientific project studied the replicability of Bem Experiment 1, which had claimed a precognitive effect, i.e., the ability to successfully guess the outcome of future random events (Bem. J Pers Soc Psychol. 2011;100: 407-25). The use of advanced methodologies-based on the advanced meta-experimental protocol (AMP) and transparent psi project (TPP) procedures-reduced the risk of false discoveries as a function of (i) confirmation bias, (ii) non-transparency, and (iii) intrinsic measurement bias. The combined AMP-TPP test strategy performed three replication studies with a total of 26,483 participants resulting in N = 420,472 critical trials. Study 1 failed to replicate the precognitive effect. An exploratory analysis of Study 1 suggested an effect in the opposite direction than was originally predicted (49.48% ± 0.26 SE; N = 37,836). Study 2 confirmed this exploratory result using a high-powered replication design (49.65% ± 0.14 SE; p = 0.013; N = 127,000). Study 3 was unable to replicate the result from Study 2 (50.07% ± 0.11 SE; p = 0.496; N = 217,800). The results of Study 2 represent a rare example in psi research of the successful replication of an exploratory result using a confirmatory protocol. The source of the one-time confirmed anomalous result in Study 2 remains to be identified. This result presents either (i) a psi-derived anomaly that defies known physical laws, or (ii) a method-derived anomaly, e.g., a false-positive statistical finding. Using conventional standards, based on the lack of replicability in Study 3 and absence of an accepted scientific
   current heuristic reason: Matched Figure 1 bibliographic search query '"meta-scientific" "replication" "database"'; lead_classification=corpus_database_or_project_signal; score=14; reasons=strong_phrase:replication project | strong_phrase:replication studies | replication_word | metadata_corpus_signal

44. review_id: review_figure1_search_leads_4884874505b4
   lead_key: title:msrp_additional_report_tables_promoted_pairs
   queue_status: needs_root_candidate_review
   name: msrp additional report tables promoted pairs
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: data/derived/replication_pairs/harvest/promoted/msrp_additional_report_tables__promoted_pairs.csv
   source_key: data/derived/replication_pairs/harvest/promoted/msrp_additional_report_tables__promoted_pairs.csv
   description: Local scan hit; file_type=table_or_package; matched_query=study_pair_id original replication; path=data/derived/replication_pairs/harvest/promoted/msrp_additional_report_tables__promoted_pairs.csv; snippet=source_dataset,project,pair_id,original_title,replication_title,original_doi,replication_doi,outcome,D_original,N_original,D_replication,N_replication,raw_file,match_author MSRP Chen et al. 2013 report table,Management Science Replication Project,msrp_chen_payment_scheme_michigan_online,Chen et al. (2013) pay
   current heuristic reason: Matched Figure 1 code search query 'study_pair_id original replication'; lead_classification=corpus_database_or_project_signal; score=15; reasons=strong_phrase:replication project | data_term:data | data_term:dataset | replication_word | original_word | local_table_or_code_surface | query_phrase_in_text

45. review_id: review_figure1_search_leads_2d6cb9f87e65
   lead_key: title:msrp_croson_donohue_promoted_pairs
   queue_status: needs_root_candidate_review
   name: msrp croson donohue promoted pairs
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: data/derived/replication_pairs/harvest/promoted/msrp_croson_donohue__promoted_pairs.csv
   source_key: data/derived/replication_pairs/harvest/promoted/msrp_croson_donohue__promoted_pairs.csv
   description: Local scan hit; file_type=table_or_package; matched_query=study_pair_id original replication; path=data/derived/replication_pairs/harvest/promoted/msrp_croson_donohue__promoted_pairs.csv; snippet=source_dataset,project,pair_id,original_title,replication_title,original_doi,replication_doi,outcome,D_original,N_original,D_replication,N_replication,raw_file,match_author MSRP Croson and Donohue 2006 report,Management Science Replication Project,msrp_croson_donohue_utd_hyp3,Croson and Donohue (2006) bullwhi
   current heuristic reason: Matched Figure 1 code search query 'study_pair_id original replication'; lead_classification=corpus_database_or_project_signal; score=15; reasons=strong_phrase:replication project | data_term:data | data_term:dataset | replication_word | original_word | local_table_or_code_surface | query_phrase_in_text

46. review_id: review_figure1_search_leads_42d730324225
   lead_key: title:msrp_schweitzer_cachon_promoted_pairs
   queue_status: needs_root_candidate_review
   name: msrp schweitzer cachon promoted pairs
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: data/derived/replication_pairs/harvest/promoted/msrp_schweitzer_cachon__promoted_pairs.csv
   source_key: data/derived/replication_pairs/harvest/promoted/msrp_schweitzer_cachon__promoted_pairs.csv
   description: Local scan hit; file_type=table_or_package; matched_query=study_pair_id original replication; path=data/derived/replication_pairs/harvest/promoted/msrp_schweitzer_cachon__promoted_pairs.csv; snippet=source_dataset,project,pair_id,original_title,replication_title,original_doi,replication_doi,outcome,D_original,N_original,D_replication,N_replication,raw_file,match_author MSRP Schweitzer & Cachon 2000 report,Management Science Replication Project,msrp_schweitzer_cachon_cornell_high_profit,Schweitzer & Cacho
   current heuristic reason: Matched Figure 1 code search query 'study_pair_id original replication'; lead_classification=corpus_database_or_project_signal; score=15; reasons=strong_phrase:replication project | data_term:data | data_term:dataset | replication_word | original_word | local_table_or_code_surface | query_phrase_in_text

47. review_id: review_figure1_search_leads_98c37a71a23b
   lead_key: title:multi_lab_replication_studies
   queue_status: needs_root_candidate_review
   name: Multi-lab replication studies
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://osf.io/t7u3x/ | https://osf.io/ar2pg/
   source_key: t7u3x | ar2pg
   description: Concern over the replicability of psychological science has risen in recent years, particularly with regard to social psychology. A combination of events led to a general sense of crisis. The importance of replication has led to many researchers to embrace multi-site replications as a presumably rigorous method for verifying the validity of scientific findings. The project reviews the published results of these multi-laboratory replication attempts in social psychology, in the hope of understanding what factors influence successful and unsuccessful replications of original studies.
   current heuristic reason: Matched Figure 1 repository search query '"multi-lab replication" "dataset" "effect size"'; lead_classification=corpus_database_or_project_signal; score=16; reasons=strong_phrase:multi-site replication | strong_phrase:replication studies | pair_term:original studies | replication_word | original_word

48. review_id: review_figure1_search_leads_5dee5429d716
   lead_key: title:nanoscience_is_latest_discipline_to_embrace_large_scale_replication_efforts
   queue_status: needs_root_candidate_review
   name: Nanoscience is latest discipline to embrace large-scale replication efforts
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1038/d41586-026-00439-6
   source_key: 10.1038/d41586-026-00439-6
   description: 
   current heuristic reason: Matched Figure 1 bibliographic search query '"large-scale replication" "original study"'; lead_classification=corpus_database_or_project_signal; score=9; reasons=strong_phrase:large-scale replication | replication_word | metadata_corpus_signal

49. review_id: review_figure1_search_leads_a2855494fa94
   lead_key: title:new_statistical_metrics_for_multisite_replication_projects
   queue_status: needs_root_candidate_review
   name: New statistical metrics for multisite replication projects
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://osf.io/apnjk/
   source_key: apnjk
   description: [Slide talk of this material: https://www.youtube.com/watch?v=xhexCDRKKW4] Increasing interest in replicability in the social sciences has engendered novel designs for replication projects in which multiple sites replicate an original study. At least 134 such "many-to-one" replications have been completed since 2014 or are currently ongoing. These designs have unique potential to help estimate whether the original study is statistically consistent with the replications and to re-assess the strength of evidence for the scientific effect of interest. However, existing statistical analyses generally focus on single replications; when applied to many-to-one designs, they provide an incomplete view of aggregate evidence and can lead to unduly pessimistic conclusions about replication success. We therefore propose new statistical metrics representing: (1) the probability that the original study's estimated effect size would be as extreme or more extreme than it actually was, if in fact the original study is statistically consistent with the replications; (2) the proportion of true effects agreeing in direction with the original study. Generalized versions of the second metric allow consideration only of true effects of non-negligible size; they estimate the proportion of true effects of scientifically meaningful size in the same direction as the estimate of the original study and, secondly, the proportion of effects of meaningful size in the direction opposite the original study's estimate. We provide an R package ("Replicate").
   current heuristic reason: Matched Figure 1 repository search query '"replication project" "coded data" "original study"'; lead_classification=corpus_database_or_project_signal; score=15; reasons=strong_phrase:replication project | pair_term:original study | pair_term:effect size | replication_word | original_word | effect_or_sample_size_phrase

50. review_id: review_figure1_search_leads_a8d0a39a1a34
   lead_key: title:nuclear_taboo_in_an_age_of_upheaval_a_large_scale_replication_project
   queue_status: needs_root_candidate_review
   name: Nuclear Taboo in an Age of Upheaval: A Large-Scale Replication Project
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://osf.io/dhy45/
   source_key: dhy45
   description: This large-scale replication project aims to investigate the alleged erosion of the "nuclear taboo" in world politics. To do so, we replicate foundational nuclear taboo surveys and survey experiments to examine how support for nuclear strikes has shifted since the beginning of the Russian invasion of Ukraine in 2022.
   current heuristic reason: Matched Figure 1 repository search query '"large-scale replication project" "original study"'; lead_classification=corpus_database_or_project_signal; score=12; reasons=strong_phrase:replication project | strong_phrase:large-scale replication | replication_word

```
