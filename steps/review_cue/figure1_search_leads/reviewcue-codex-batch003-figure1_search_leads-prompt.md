# figure1_search_leads Codex Review Prompt

Save returned JSON as `steps/review_cue/figure1_search_leads/reviewcue-decisions-figure1_search_leads-codex-batch003.json`.

```text
You are a Codex background reviewer for review cue `figure1_search_leads`.
Reusable bounded review queue for ambiguous Figure 1 corpus/database, repository-package, result-table, individual-paper, and context-source leads. Deterministic scripts should remove obvious duplicates and false positives first. Codex should investigate moderate batches and either make auditable decisions or emit compact GPT prompt requests for uncertain cases. GPT prompt batches can be larger because they are user-mediated review artifacts.

Work only this bounded batch. Investigate URLs and source metadata when useful.
Do not edit root tables. Return or save JSON decisions using the contract below.
Each accepted decision will later be applied as a per-lead receipt file, so future cue builds can skip it by checking for that target file.
If you are not confident, set decision to `needs_more_evidence` and include `user_gpt_prompt_request` with a compact prompt the user can give to GPT Pro.

Save decisions as: `steps/review_cue/figure1_search_leads/reviewcue-decisions-figure1_search_leads-codex-batch003.json`

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

```
