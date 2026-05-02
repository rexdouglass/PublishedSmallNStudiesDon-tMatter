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
1. review_id: review_figure1_search_leads_dda29ca9aa76
   lead_key: title:analyzing_data_of_a_multilab_replication_project_with_individual_participant_data_meta_analysis
   queue_status: needs_root_candidate_review
   name: Analyzing Data of a Multilab Replication Project With Individual Participant Data Meta-Analysis
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1027/2151-2604/a000483
   source_key: 10.1027/2151-2604/a000483 | https://openalex.org/W4210766447
   description: <jats:p>Abstract. Multilab replication projects such as Registered Replication Reports (RRR) and Many Labs projects are used to replicate an effect in different labs. Data of these projects are usually analyzed using conventional meta-analysis methods. This is certainly not the best approach because it does not make optimal use of the available data as a summary rather than participant data are analyzed. I propose to analyze data of multilab replication projects with individual participant data (IPD) meta-analysis where the participant data are analyzed directly. The prominent advantages of IPD meta-analysis are that it generally has larger statistical power to detect moderator effects and allows drawing conclusions at the participant and lab level. However, a disadvantage is that IPD meta-analysis is more complex than conventional meta-analysis. In this tutorial, I illustrate IPD meta-analysis using the RRR by McCarthy and colleagues, and I provide R code and recommendations to facilitate researchers to apply these methods.</jats:p>
   current heuristic reason: Matched Figure 1 bibliographic search query '"replication project" "coded data"'; lead_classification=corpus_database_or_project_signal; score=21; reasons=strong_phrase:replication project | strong_phrase:registered replication report | strong_phrase:many labs | data_term:data | data_term:code | replication_word | metadata_corpus_signal

2. review_id: review_figure1_search_leads_ce0d98ff2acc
   lead_key: title:analyzing_data_of_a_multilab_replication_project_with_individual_participant_data_meta_analysis_a_tutorial
   queue_status: needs_root_candidate_review
   name: Analyzing data of a multilab replication project with individual participant data meta-analysis: A tutorial
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.31222/osf.io/9tmua
   source_key: https://openalex.org/W3094282098 | 10.31222/osf.io/9tmua
   description: Multilab replication projects such as Registered Replication Reports (RRR) and Many Labs projects are used to replicate an effect in different labs. Data of these projects are usually analyzed using conventional meta-analysis methods. This is certainly not the best approach, because it does not make optimal use of the available data as summary rather than participant data are analyzed. I propose to analyze data of multilab replication projects with individual participant data (IPD) meta-analysis where the participant data are analyzed directly. Prominent advantages of IPD meta-analysis are that it generally has larger statistical power to detect moderator effects and allows drawing conclusions at the participant and lab level. However, a disadvantage is that IPD meta-analysis is more complex than conventional meta-analysis. In this tutorial, I illustrate IPD meta-analysis using the RRR by McCarthy and colleagues, and I provide R code and recommendations to facilitate researchers to apply these methods.
   current heuristic reason: Matched Figure 1 citation search query '"registered replication report" "many labs"'; lead_classification=corpus_database_or_project_signal; score=21; reasons=strong_phrase:replication project | strong_phrase:registered replication report | strong_phrase:many labs | data_term:data | data_term:code | replication_word | metadata_corpus_signal

3. review_id: review_figure1_search_leads_77bdfd624563
   lead_key: title:artificial_intelligence_in_psychology_research
   queue_status: needs_root_candidate_review
   name: Artificial intelligence in psychology research
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.31234/osf.io/rva3w
   source_key: https://openalex.org/W4321102425
   description: Large Language Models have vastly grown in capabilities. One potential application of such AI systems is to support data collection in the social sciences, where perfect experimental control is currently unfeasible and the collection of large, representative datasets is generally expensive. In this paper, we re-replicate 14 studies from the Many Labs 2 replication project (Klein et al., 2018) with OpenAI’s text-davinci-003 model, colloquially known as GPT3.5. For the 10 studies that we could analyse, we collected a total of 10,136 responses, each of which was obtained by running GPT3.5 with the corresponding study’s survey inputted as text. We find that our GPT3.5-based sample replicates 30% of the original results as well as 30% of the Many Labs 2 results, although there is heterogeneity in both these numbers (as we replicate some original findings that Many Labs 2 did not and vice versa). We also find that unlike the corresponding human subjects, GPT3.5 answered some survey questions with extreme homogeneity—with zero variation in different runs’ responses—raising concerns that a hypothetical AI-led future may in certain ways be subject to a diminished diversity of thought. Overall, while our results suggest that Large Language Model psychology studies are feasible, their findings should not be assumed to straightforwardly generalise to the human case. Nevertheless, AI-based data collection may eventually become a viable and economically relevant method in the empirical social sciences, making the understanding of its capabilities and applications central.
   current heuristic reason: Matched Figure 1 domain search query '"many-lab" dataset original'; lead_classification=corpus_database_or_project_signal; score=18; reasons=strong_phrase:replication project | strong_phrase:many labs | data_term:data | data_term:dataset | replication_word | original_word | metadata_corpus_signal

4. review_id: review_figure1_search_leads_f7268b4a35f7
   lead_key: title:author_response_investigating_the_replicability_of_preclinical_cancer_biology
   queue_status: needs_root_candidate_review
   name: Author response: Investigating the replicability of preclinical cancer biology
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.7554/elife.71601.sa2
   source_key: https://openalex.org/W4200021434
   description: Article Figures and data Abstract Introduction Results Discussion Materials and methods Data availability References Decision letter Author response Article and author information Metrics Abstract Replicability is an important feature of scientific research, but aspects of contemporary research culture, such as an emphasis on novelty, can make replicability seem less important than it should be. The Reproducibility Project: Cancer Biology was set up to provide evidence about the replicability of preclinical research in cancer biology by repeating selected experiments from high-impact papers. A total of 50 experiments from 23 papers were repeated, generating data about the replicability of a total of 158 effects. Most of the original effects were positive effects (136), with the rest being null effects (22). A majority of the original effect sizes were reported as numerical values (117), with the rest being reported as representative images (41). We employed seven methods to assess replicability, and some of these methods were not suitable for all the effects in our sample. One method compared effect sizes: for positive effects, the median effect size in the replications was 85% smaller than the median effect size in the original experiments, and 92% of replication effect sizes were smaller than the original. The other methods were binary – the replication was either a success or a failure – and five of these methods could be used to assess both positive and null effects when effect sizes were reported as numerical values. For positive effects, 40% of replications (39/97) su
   current heuristic reason: Matched Figure 1 citation search query '"Reproducibility Project: Cancer Biology" "effect size"'; lead_classification=corpus_database_or_project_signal; score=20; reasons=strong_phrase:reproducibility project | pair_term:original effect | pair_term:replication effect | pair_term:effect size | data_term:data | replication_word | original_word | effect_or_sample_size_phrase | metadata_corpus_signal

5. review_id: review_figure1_search_leads_4599c36edb44
   lead_key: title:bringing_an_intersectional_lens_to_open_science_an_analysis_of_representation_in_the_reproducibility_project
   queue_status: needs_root_candidate_review
   name: Bringing an Intersectional Lens to “Open” Science: An Analysis of Representation in the Reproducibility Project
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1177/03616843211035678
   source_key: 10.1177/03616843211035678
   description: <jats:p> Feminist psychologists have called for researchers to consider the social and historical context and the multidimensionality of participants in research studies. The Reproducibility Project documents the degree to which the findings from mainstream psychological studies are reproduced. Drawing on intersectionality theory, we question the value of reproducing findings while ignoring who is represented, intersecting social and group identities, sociohistorical context, and the power and privilege that likely influence participants’ responses in psychology experiments. To critically examine the Reproducibility Project in psychology, we analyzed the 100 replication reports produced between 2011 and 2014 (Open Science Collaboration, 2015). We developed an intersectional analytic framework to investigate (a) representation, (b) whether demographic and identity factors were considered through a multidimensional or intersectional lens, (c) explanations of non-replication, and (d) whether socio-cultural context was considered. Results show that reports predominantly include WEIRD samples (people from Western, educated, industrialized, rich, and democratic countries). Context and identity were rarely considered, even when study design relied on these factors, and intersectional identities and structures (considering power, structural issues, discrimination, and historical context) were absent from nearly all reports. Online slides for instructors who want to use this article f
   current heuristic reason: Matched Figure 1 citation search query '"Reproducibility Project: Psychology" "original study"'; lead_classification=corpus_database_or_project_signal; score=9; reasons=strong_phrase:reproducibility project | replication_word | metadata_corpus_signal

6. review_id: review_figure1_search_leads_f5860736bcb1
   lead_key: title:caballero_2021_replication_project
   queue_status: needs_root_candidate_review
   name: Caballero 2021 Replication Project
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://osf.io/kdbsa/
   source_key: kdbsa
   description: This project is a direct replication of Study 2 from Caballero et al. (2021), which examined whether experiencing economic scarcity leads individuals to adopt a more concrete (lower-level) construal style compared to those in conditions of economic sufficiency. The study uses the Bimboola economic-scarcity manipulation, assigning participants to imagine living in either a highly resource-constrained economic group or a financially comfortable group. Construal level is assessed using the Behavioral Identification Form (BIF; Vallacher &amp; Wegner, 1989), administered both before and after the economic manipulation to capture within-person changes in abstraction. The purpose of the replication is to evaluate whether the original finding, namely a significant interaction between time (pre–post) and economic condition (scarcity vs. nonscarcity), can be reproduced in a U.S.-based online sample recruited through Prolific. According to the original study, participants assigned to economic scarcity showed a decrease in abstract construal after the manipulation, whereas participants assigned to nonscarcity showed an increase. No baseline differences in construal level were observed prior to the manipulation. The planned replication follows the original procedure as closely as possible: participants complete 12 BIF items at baseline, complete the Bimboola assignment with stimuli adapted for online presentation, and then complete another 12 BIF items. Manipulation checks assessing perceived poverty and wealth of one’s assigned group are also included, mirroring the original study to c
   current heuristic reason: Matched Figure 1 repository search query '"replication project" "coded data" "original study"'; lead_classification=corpus_database_or_project_signal; score=11; reasons=strong_phrase:replication project | pair_term:original study | replication_word | original_word

7. review_id: review_figure1_search_leads_ed3a377a1fcd
   lead_key: title:can_cancer_researchers_accurately_judge_whether_preclinical_reports_will_reproduce
   queue_status: needs_root_candidate_review
   name: Can cancer researchers accurately judge whether preclinical reports will reproduce?
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1371/journal.pbio.2002212
   source_key: https://openalex.org/W2732894280
   description: There is vigorous debate about the reproducibility of research findings in cancer biology. Whether scientists can accurately assess which experiments will reproduce original findings is important to determining the pace at which science self-corrects. We collected forecasts from basic and preclinical cancer researchers on the first 6 replication studies conducted by the Reproducibility Project: Cancer Biology (RP:CB) to assess the accuracy of expert judgments on specific replication outcomes. On average, researchers forecasted a 75% probability of replicating the statistical significance and a 50% probability of replicating the effect size, yet none of these studies successfully replicated on either criterion (for the 5 studies with results reported). Accuracy was related to expertise: experts with higher h-indices were more accurate, whereas experts with more topic-specific expertise were less accurate. Our findings suggest that experts, especially those with specialized knowledge, were overconfident about the RP:CB replicating individual experiments within published reports; researcher optimism likely reflects a combination of overestimating the validity of original studies and underestimating the difficulties of repeating their methodologies.
   current heuristic reason: Matched Figure 1 bibliographic search query '"reproducibility project" "effect sizes"'; lead_classification=corpus_database_or_project_signal; score=22; reasons=strong_phrase:reproducibility project | strong_phrase:replication studies | pair_term:original studies | pair_term:effect size | replication_word | original_word | effect_or_sample_size_phrase | metadata_corpus_signal

8. review_id: review_figure1_search_leads_75bf3c17e235
   lead_key: title:can_large_language_models_replace_human_subjects_a_large_scale_replication_of_scenario_based_experiments_in_psychology_a
   queue_status: needs_root_candidate_review
   name: Can Large Language Models Replace Human Subjects? A Large-Scale Replication of Scenario-Based Experiments in Psychology and Management
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://springernature.figshare.com/articles/dataset/Can_Large_Language_Models_Replace_Human_Subjects_A_Large-Scale_Replication_of_Scenario-Based_Experiments_in_Psychology_and_Management/27157524/1 | https://springernature.figshare.com/articles/dataset/Can_Large_Language_Models_Replace_Human_Subjects_A_Large-Scale_Replication_of_Scenario-Based_Experiments_in_Psychology_and_Management/27157524
   source_key: 10.6084/m9.figshare.27157524.v1 | 10.6084/m9.figshare.27157524
   description: This repository contains data and code for a research project replicating human psychological experiments using Large Language Models (LLMs). The project systematically evaluates how GPT-4, Claude, and DeepSeek respond to the same experimental conditions as human participants across multiple psychological studies. ## Project Overview This research investigates whether LLMs can replicate results from human psychological experiments. By presenting LLMs with identical experimental conditions used in the original studies, we compare LLM responses with human responses to assess their understanding of human psychology and potential utility as research tools. Models used in this research: - **GPT-4**: Default temperature of 1.0, with additional analyses at temperatures 0 and 0.5 - **Claude**: Default temperature settings - **DeepSeek**: Temperature set to 1.3 (optimized for conversational scenarios) ## Repository Structure The repository is organized into three main directories: ### 1. LLM API Calls (01 LLM API Calls) Contains code and documentation for making API calls to different LLM models: - **prompt/**: Prompts used to query the LLMs - **script/**: Scripts for making API calls (`script_gpt.py`, `script_gpt_image.py`, `script_claude.py`, etc.) - **output data/**: Raw output data from the LLM API calls - **README_LLMs API Calls.docx**: Documentation for the API call process ### 2. Study-level Analysis (02 Study-level analysis) Contains individual analyses for each replicated study. Each study folder follows the naming convention `[Journal]_[Paper]_[Study]`, where: - Journal: O
   current heuristic reason: Matched Figure 1 link_graph search query '10.1038/s43588-025-00840-7'; lead_classification=corpus_database_or_project_signal; score=18; reasons=strong_phrase:large-scale replication | pair_term:original studies | data_term:data | data_term:code | data_term:repository | replication_word | original_word | known_corpus_paper_link_graph

9. review_id: review_figure1_search_leads_3b461705e061
   lead_key: title:cancer_reproducibility_project_scales_back_ambitions
   queue_status: needs_root_candidate_review
   name: Cancer reproducibility project scales back ambitions
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1038/nature.2015.18938
   source_key: 10.1038/nature.2015.18938
   description: 
   current heuristic reason: Matched Figure 1 bibliographic search query '"reproducibility project" "effect sizes"'; lead_classification=corpus_database_or_project_signal; score=7; reasons=strong_phrase:reproducibility project | metadata_corpus_signal

10. review_id: review_figure1_search_leads_62a5c00b9ba8
   lead_key: title:challenges_and_suggestions_for_defining_replication_success_when_effects_may_be_heterogeneous_comment_on_hedges_and_scha
   queue_status: needs_root_candidate_review
   name: Challenges and suggestions for defining replication “success” when effects may be heterogeneous: Comment on Hedges and Schauer (2019).
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1037/met0000223
   source_key: https://openalex.org/W2979112662
   description: Psychological scientists are now trying to replicate published research from scratch to confirm the findings. In an increasingly widespread replication study design, each of several collaborating sites (such as universities) independently tries to replicate an original study, and the results are synthesized across sites. Hedges and Schauer (2019) proposed statistical analyses for these replication projects; their analyses focus on assessing the extent to which results differ across the replication sites, by testing for heterogeneity among a set of replication studies, while excluding the original study. We agree with their premises regarding the limitations of existing analysis methods and regarding the importance of accounting for heterogeneity among the replications. This objective may be interesting in its own right. However, we argue that by focusing only on whether the replication studies have similar effect sizes to one another, these analyses are not particularly appropriate for assessing whether the replications in fact support the scientific effect under investigation or for assessing the power of multisite replication projects. We reanalyze Hedges and Schauer's (2019) example dataset using alternative metrics of replication success that directly address these objectives. We reach a more optimistic conclusion regarding replication success than they did, illustrating that the alternative metrics can lead to quite different conclusions from those of Hedges and Schauer (2019). (PsycINFO Database Record (c) 2019 APA, all rights reserved).
   current heuristic reason: Matched Figure 1 bibliographic search query '"replication project" "original study" "effect size"'; lead_classification=corpus_database_or_project_signal; score=23; reasons=strong_phrase:replication project | strong_phrase:replication studies | pair_term:original study | pair_term:effect size | data_term:data | data_term:dataset | data_term:database | replication_word | original_word | metadata_corpus_signal

11. review_id: review_figure1_search_leads_6061ab8657b3
   lead_key: title:comparing_meta_analyses_and_pre_registered_multiple_labs_replication_projects
   queue_status: needs_root_candidate_review
   name: Comparing Meta-Analyses and Pre-Registered Multiple Labs Replication Projects
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.31219/osf.io/brzwt
   source_key: https://openalex.org/W4229834291
   description: Many researchers rely on meta-analysis to summarize research evidence. However, recent replication projects in the behavioral sciences suggest that effect sizes of original studies are overestimated, and this overestimation is typically attributed to publication bias and selective reporting of scientific results. As the validity of meta-analyses depends on the primary studies, there is a concern that systematic overestimation of effect sizes may translate into biased meta-analytic effect sizes. We compare the results of meta-analyses to large-scale pre-registered replications in psychology carried out at multiple labs. The multiple labs replications provide relatively precisely estimated effect sizes, which do not suffer from publication bias or selective reporting. Searching the literature, 17 meta-analyses – spanning more than 1,200 effect sizes and more than 370,000 participants - on the same topics as multiple labs replications are identified. We find that the meta-analytic effect sizes are significantly different from the replication effect sizes for 12 out of the 17 meta-replication pairs. These differences are systematic and on average meta-analytic effect sizes are about three times as large as the replication effect sizes.
   current heuristic reason: Matched Figure 1 bibliographic search query '"replication project" "original study" "effect size"'; lead_classification=corpus_database_or_project_signal; score=17; reasons=strong_phrase:replication project | pair_term:original studies | pair_term:replication effect | pair_term:effect size | replication_word | original_word | metadata_corpus_signal

12. review_id: review_figure1_search_leads_27d5775f87b9
   lead_key: title:compilation_of_diener_et_al_2010_osf_multi_site_replication_projects
   queue_status: needs_root_candidate_review
   name: Compilation of Diener et al. (2010) OSF Multi-Site Replication Projects
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://osf.io/qdx7p/
   source_key: qdx7p
   description: OSF page consists of the data from the Diener et al. (2010) replication datasets that exist and are available on OSF. This page is also home to the analysis that the original researchers conducted at the University of Minnesota - Twin Cities. We hope that others can use this data and benefit from OSF.
   current heuristic reason: Matched Figure 1 domain search query '"multi-site" replication dataset original'; lead_classification=corpus_database_or_project_signal; score=20; reasons=strong_phrase:replication project | strong_phrase:multi-site replication | data_term:data | data_term:dataset | data_term:osf | replication_word | original_word | repository_data_surface | metadata_corpus_signal

13. review_id: review_figure1_search_leads_3bb59d13d306
   lead_key: title:confounds_in_failed_replications
   queue_status: needs_root_candidate_review
   name: Confounds in “failed” replications
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.31234/osf.io/gth8u
   source_key: https://openalex.org/W4238249240
   description: Reproducibility is essential to science, yet a distressingly large number of research findings do not seem to replicate. Here I discuss one underappreciated reason for this state of affairs. I make my case by noting that, due to artifacts, several of the replication failures of the vastly advertised Open Science Collaboration’s Reproducibility Project: Psychology turned out to be invalid. Although these artifacts would have been obvious on perusal of the data, such perusal was deemed undesirable because of its post hoc nature and was left out. However, while data do not lie, unforeseen confounds can render them unable to speak to the question of interest. I look further into one unusual case in which a major artifact could be removed statistically—the nonreplication of the effect of fertility on partnered women’s preference for single over attached men. I show that the “failed replication” datasets contain a gross bias in stimulus allocation which is absent in the original dataset; controlling for it replicates the original study’s main finding. I conclude that, before being used to make a scientific point, all data should undergo a minimal quality control—a provision, it appears, not always required of those collected for purpose of replication. Because unexpected confounds and biases can be laid bare only after the fact, we must get over our understandable reluctance to engage in anything post hoc. The reproach attached to p-hacking cannot exempt us from the obligation to (openly) take a good look at our data.
   current heuristic reason: Matched Figure 1 citation search query '"Reproducibility Project: Psychology" dataset replication'; lead_classification=corpus_database_or_project_signal; score=15; reasons=strong_phrase:reproducibility project | pair_term:original study | data_term:data | data_term:dataset | replication_word | original_word | metadata_corpus_signal

14. review_id: review_figure1_search_leads_7d6514b80c79
   lead_key: title:construct_validity_and_the_validity_of_replication_studies_a_systematic_review
   queue_status: needs_root_candidate_review
   name: Construct validity and the validity of replication studies: A systematic review.
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1037/amp0001006 | https://doi.org/10.31234/osf.io/369qj
   source_key: https://openalex.org/W4225083776 | https://openalex.org/W4221089041
   description: Currently, there is little guidance for navigating measurement challenges that threaten construct validity in replication research. To identify common challenges and ultimately strengthen replication research, we conducted a systematic review of the measures used in the 100 original and replication studies from the Reproducibility Project: Psychology (Open Science Collaboration, 2015). Results indicate that it was common for scales used in the original studies to have little or no validity evidence. Our systematic review demonstrates and corroborates evidence that issues of construct validity are sorely neglected in original and replicated research. We identify four measurement challenges replicators are likely to face: a lack of essential measurement information, a lack of validity evidence, measurement differences, and translation. Next, we offer solutions for addressing these challenges that will improve measurement practices in original and replication research. Finally, we close with a discussion of the need to develop measurement methodologies for the next generation of replication research. (PsycInfo Database Record (c) 2022 APA, all rights reserved).
   current heuristic reason: Matched Figure 1 citation search query '"Reproducibility Project: Psychology" "original study"'; lead_classification=corpus_database_or_project_signal; score=20; reasons=strong_phrase:reproducibility project | strong_phrase:replication studies | pair_term:original studies | data_term:data | data_term:database | replication_word | original_word | metadata_corpus_signal

15. review_id: review_figure1_search_leads_09abed40d362
   lead_key: title:corpus_suggestion_tracker
   queue_status: needs_root_candidate_review
   name: corpus suggestion tracker
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: reports/corpus_suggestion_tracker.md
   source_key: reports/corpus_suggestion_tracker.md
   description: Local scan hit; file_type=text_or_code; matched_query=study_pair_id original replication; path=reports/corpus_suggestion_tracker.md; snippet=1,969 original-claim rows across 762 original-paper DOI units. Paper-level slope `-0.421`; p<.10 share about 94%. | Not a random journal-paper sample. Rows are original findings selected into replication projects/databases or submitted as replications, so this is a replication-target/focal-claim frame. Not all rows are treatment/intervention effects. | Audit effect-type conversions, especially p-only and et
   current heuristic reason: Matched Figure 1 code search query 'study_pair_id original replication'; lead_classification=corpus_database_or_project_signal; score=13; reasons=strong_phrase:replication project | data_term:data | data_term:database | data_term:code | replication_word | original_word | query_phrase_in_text

16. review_id: review_figure1_search_leads_53d32984a608
   lead_key: title:cross_platform_metabolomics_imputation_using_importance_weighted_autoencoders
   queue_status: needs_root_candidate_review
   name: Cross-platform metabolomics imputation using importance-weighted autoencoders
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1101/2025.03.06.25323475 | https://doi.org/10.1038/s41540-025-00644-5
   source_key: https://doi.org/10.1101/2025.03.06.25323475 | PMC12894875
   description: <h4>Background</h4> Metabolomics data are often generated through different analytical platforms and different methods of identification and quantification which makes their synthesis and large-scale replication challenging. To address this, we applied generative deep learning to impute metabolites assayed by Metabolon, a commonly used commercial platform, using metabolomic features acquired by an untargeted liquid chromatography-mass spectrometry (LC-MS) platform. <h4>Methods</h4> We utilised a subset of 979 samples from the Airwave Health Monitoring Study which were assayed by both Metabolon and National Phenome Centre at Imperial College (NPC) LC-MS assays to develop an ensemble of importance-weighted autoencoders (IWAEs) which can perform cross-platform metabolomics imputation between the two assays. Using the ensemble, we generated a Metabolon equivalent dataset in 2,971 additional Airwave samples that lacked prior Metabolon measurements. We conducted observational associations with two clinical outcomes, body mass index (BMI) and C-reactive protein (CRP). We validated the ensemble and imputed data by investigating the concordance of the observational associations. This was done using both the imputed Metabolon dataset and the measured metabolite levels by Metabolon, and NPC in the Airwave study and Nightingale platform in the UK Biobank. <h4>Results</h4> Our imputation ensemble generated samples highly correlated with their real values across all Metabolon metabolites within a held-out test set with a mean sample correlation of 0.61 (IQR 0.55-0.67). The well-imputed s
   current heuristic reason: Matched Figure 1 bibliographic search query '"large-scale replication" "dataset"'; lead_classification=corpus_database_or_project_signal; score=12; reasons=strong_phrase:large-scale replication | data_term:data | data_term:dataset | data_term:code | replication_word | metadata_corpus_signal

17. review_id: review_figure1_search_leads_c003e8bf12be
   lead_key: title:data_from_investigating_variation_in_replicability_a_many_labs_replication_project
   queue_status: needs_root_candidate_review
   name: Data from Investigating Variation in Replicability: A “Many Labs” Replication Project
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.5334/jopd.ad | https://doi.org/10.31234/osf.io/25ju4
   source_key: 10.5334/jopd.ad | https://openalex.org/W2126632863 | https://openalex.org/W4226251881
   description: 
   current heuristic reason: Matched Figure 1 bibliographic search query '"replication project" "coded data"'; lead_classification=corpus_database_or_project_signal; score=15; reasons=strong_phrase:replication project | strong_phrase:many labs | data_term:data | replication_word | metadata_corpus_signal

18. review_id: review_figure1_search_leads_7f8c8d6ea1da
   lead_key: title:data_from_evaluating_the_foraging_performance_of_individual_honey_bees_in_different_environments_with_automated_field_rf
   queue_status: needs_root_candidate_review
   name: Data from: Evaluating the foraging performance of individual honey bees in different environments with automated field RFID systems
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.5061/dryad.83bk3j9s6
   source_key: doi:10.5061/dryad.83bk3j9s6
   description: <p style="margin-bottom:11px;text-align:left;">Measuring the individual foraging performances of pollinators is crucial to guide environmental policies that aim at enhancing pollinator health and pollination services. Automated systems have been developed to track the activity of individual honey bees, but their deployment is extremely challenging. This has limited the assessment of individual foraging performances in full-strength bee colonies in the field. Most studies available to date have been constrained to use downsized bee colonies located in urban and suburban areas. Environmental policy-making, on the other hand, needs a more comprehensive assessment of honey bee performances in a broader range of environments, including in remote agricultural and wild areas. Here we detail a new autonomous field method to record high quality data on the flight ontogeny and foraging performance of honey bees, using Radio-Frequency Identification (RFID). We separate bee traffic into returning and exiting tunnels to improve data quality, solving many previous limitations of RFID systems caused by traffic jams and the parasitic coupling of RFID antennae. With this method, we assembled a large RFID dataset made of control bee colonies from experiments conducted in different locations and seasons. We hope our results will be a starting point to understand how ontogenetic and environmental factors affect the individual performances of honey bees, and that our method will enable the large-scale replication of individual pollinator performance studies.</p>
   current heuristic reason: Matched Figure 1 repository search query '"large-scale replication" "data"'; lead_classification=corpus_database_or_project_signal; score=10; reasons=strong_phrase:large-scale replication | data_term:data | data_term:dataset | replication_word | dataset_metadata_surface

19. review_id: review_figure1_search_leads_0a55b6cc7790
   lead_key: title:die_vertrauensw_rdigkeit_von_replikationen_der_einfluss_von_pr_registrierungen_auf_den_replikationserfolg
   queue_status: needs_root_candidate_review
   name: Die Vertrauenswürdigkeit von Replikationen : Der Einfluss von Präregistrierungen auf den Replikationserfolg
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.20378/irb-105013
   source_key: https://openalex.org/W4405610981
   description: Theorie: Die Psychologie befindet sich in einer Replikationskrise, die unter anderem auf die „Publish or Perish“ Kultur zurückzuführen ist. Diese Kultur führt dazu, dass in großer Anzahl spannende und signifikante Studien veröffentlicht werden müssen, um im akademischen System Anerkennung zu finden. P-Hacking und andere fragwürdige Forschungspraktiken sind Auswirkungen dieser Kultur. In der vorliegenden Studie wurde untersucht, ob Replikationsstudien ebenfalls von Hacking betroffen sind. Es wurden dazu verschiedene Anreize für das Manipulieren von Replikationen vorgestellt. Besonders wurde auf Null-Hacking eingegangen, das durch die hohe Aufmerksamkeit auf nicht replizierte Befunde, begünstigt werden könnte. Methodik: Die Methode Präregistrierung gilt als ein direktes Mittel, um Freiheitsgrade von Forschenden einzuschränken und dabei Hacking entgegenzuwirken. Daher untersuchte die vorliegende präregistrierte Studie anhand der bisher umfassendsten Replikationsdatenbank (FORRT Replication Database), ob der Präregistrierungsstatus der Replikationsstudie den Zusammenhang zwischen Originaleffekt und Replikationseffekt moderiert. Nach allen Exklusionen wurden 361 Replikationseffekte berücksichtigt, von denen 124 präregistriert waren. Es wurde darüber hinaus ermittelt, ob die Ähnlichkeit (Closeness) zwischen der Originalstudie und der Replikationsstudie sowie verschiedene Präregistrierungsvorlagen den Zusammenhang zwischen Originaleffekt und Replikationseffekt moderieren. Zudem wurde explorativ untersucht, ob präregistrierte Replikationen sich hinsichtlich des Replikationserfolgs
   current heuristic reason: Matched Figure 1 citation search query '"FORRT" "replication database"'; lead_classification=corpus_database_or_project_signal; score=12; reasons=strong_phrase:replication database | data_term:data | data_term:database | replication_word | metadata_corpus_signal | query_phrase_in_text

20. review_id: review_figure1_search_leads_958c630e6e83
   lead_key: title:does_expertise_matter_in_replication_an_examination_of_the_reproducibility_project_psychology
   queue_status: needs_root_candidate_review
   name: Does expertise matter in replication? An examination of the reproducibility project: Psychology
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1016/j.jesp.2016.07.003
   source_key: 10.1016/j.jesp.2016.07.003
   description: 
   current heuristic reason: Matched Figure 1 citation search query '"Reproducibility Project: Psychology" "original study"'; lead_classification=corpus_database_or_project_signal; score=9; reasons=strong_phrase:reproducibility project | replication_word | metadata_corpus_signal

21. review_id: review_figure1_search_leads_e2c9f63ac70c
   lead_key: title:does_high_variability_training_improve_the_learning_of_non_native_phoneme_contrasts_over_low_variability_training_a_repl
   queue_status: needs_root_candidate_review
   name: Does high variability training improve the learning of non-native phoneme contrasts over low variability training? A replication
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1016/j.jml.2022.104352
   source_key: https://openalex.org/W4285585316
   description: Acquiring non-native speech contrasts can be difficult. A seminal study by Logan, Lively and Pisoni (1991) established the effectiveness of phonetic training for improving non-native speech perception: Japanese learners of English were trained to perceive /r/-/l/ using minimal pairs over 15 training sessions. A pre/post-test design established learning and generalisation. In a follow-up study, Lively, Logan and Pisoni (1993) presented further evidence which suggested that talker variability in training stimuli was crucial in leading to greater generalisation. These findings have been very influential and “high variability phonetic training” is now a standard methodology in the field. However, while the general benefit of phonetic training is well replicated, the evidence for an advantage of high over lower variability training remains mixed. In a large-scale replication of the original studies using updated statistical analyses we test whether learners generalise more after phonetic training using multiple talkers over a single talker. We find that listeners learn in both multiple and single talker conditions. However, in training, we find no difference in how well listeners learn for high vs low variability training. When comparing generalisation to novel talkers after training in relation to pre-training accuracy, we find ambiguous evidence for a high-variability benefit over low-variability training: This means that if a high-variability benefit exists, the effect is much smaller than originally thought, such that it cannot be detected in our sample of 166 listeners.
   current heuristic reason: Matched Figure 1 bibliographic search query '"large-scale replication" "original study"'; lead_classification=corpus_database_or_project_signal; score=13; reasons=strong_phrase:large-scale replication | pair_term:original studies | replication_word | original_word | metadata_corpus_signal

22. review_id: review_figure1_search_leads_46613d3e6bc2
   lead_key: title:does_repetition_increase_perceived_truth_equally_for_conspiracy_and_trivia_statements_a_registered_replication_report
   queue_status: needs_root_candidate_review
   name: Does repetition increase perceived truth equally for conspiracy and trivia statements? A registered replication report.
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.3758/s13423-025-02836-w
   source_key: PMC12779699
   description: Repetition increases the perceived truth of information. This illusory truth effect is a well-documented and robust phenomenon. Although research has primarily focused on trivia statements, the effects of repetition on belief have also been identified for consequential statements such as fake news headlines. Moreover, research reveals repetition increases accuracy ratings for conspiracy statements. However, in past work, the illusory truth effect was smaller for conspiracy statements than trivia statements. This result raises the intriguing possibility that there is something unique about conspiracy statements relative to trivia statements that makes them more resistant to the effects of repetition. However, this difference in the illusory truth effect between conspiracy and trivia statements may be due to differences in baseline plausibility rather than anything specific about conspiracy statements. Overall, the conspiracy statements were seen as less plausible than the trivia statements (both true and false trivia statements) in the prior experiment. In this registered report, we examined the illusory truth effect for conspiracy and trivia statements using the same procedure as in previous research, but we matched the statements on baseline plausibility. In line with our hypothesis, the effect of repetition on perceived truth was similar for conspiracy and trivia statements when they were equally implausible (or plausible). Results from this study replicate the generality of the illusory truth effect to statements that can cause harm and suggest that the psychological eff
   current heuristic reason: Matched Figure 1 bibliographic search query '"registered replication report" "original study"'; lead_classification=corpus_database_or_project_signal; score=7; reasons=strong_phrase:registered replication report | replication_word

23. review_id: review_figure1_search_leads_5a6989d0ac69
   lead_key: title:earth_science_citation_replication_project
   queue_status: needs_root_candidate_review
   name: Earth Science Citation Replication Project
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://osf.io/u49zv/
   source_key: u49zv
   description: This registration describes the hypotheses to be tested and the methods planned to replicate White 2019 (https://crl.acrl.org/index.php/crl/article/view/16892/19368), a study of the publication and citation practices of Earth Science researchers. We propose a programmatic approach to scale White’s original study and apply similar methods to three additional universities in the United States.
   current heuristic reason: Matched Figure 1 repository search query '"replication project" "coded data" "original study"'; lead_classification=corpus_database_or_project_signal; score=11; reasons=strong_phrase:replication project | pair_term:original study | replication_word | original_word

24. review_id: review_figure1_search_leads_6c2f7ee495da
   lead_key: title:ecls_k_replication_project
   queue_status: needs_root_candidate_review
   name: ECLS-K Replication Project
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://osf.io/gvzwe/ | https://osf.io/hsgj2/
   source_key: gvzwe | hsgj2
   description: For ReScience X article
   current heuristic reason: Matched Figure 1 citation search query '"ReScience"'; lead_classification=corpus_database_or_project_signal; score=10; reasons=strong_phrase:replication project | replication_word | metadata_corpus_signal | query_phrase_in_text

25. review_id: review_figure1_search_leads_24788ac9a7b9
   lead_key: title:eleven_years_of_student_replication_projects_provide_evidence_on_the_correlates_of_replicability_in_psychology
   queue_status: needs_root_candidate_review
   name: Eleven years of student replication projects provide evidence on the correlates of replicability in psychology.
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1098/rsos.231240
   source_key: PMC10645069
   description: Cumulative scientific progress requires empirical results that are robust enough to support theory construction and extension. Yet in psychology, some prominent findings have failed to replicate, and large-scale studies suggest replicability issues are widespread. The identification of predictors of replication success is limited by the difficulty of conducting large samples of independent replication experiments, however: most investigations reanalyse the same set of 170 replications. We introduce a new dataset of 176 replications from students in a graduate-level methods course. Replication results were judged to be successful in 49% of replications; of the 136 where effect sizes could be numerically compared, 46% had point estimates within the prediction interval of the original outcome (versus the expected 95%). Larger original effect sizes and within-participants designs were especially related to replication success. Our results indicate that, consistent with prior reports, the robustness of the psychology literature is low enough to limit cumulative progress by student investigators.
   current heuristic reason: Matched Figure 1 bibliographic search query '"replication project" "coded data"'; lead_classification=corpus_database_or_project_signal; score=17; reasons=strong_phrase:replication project | pair_term:original effect | pair_term:effect size | data_term:data | data_term:dataset | replication_word | original_word | metadata_corpus_signal

26. review_id: review_figure1_search_leads_95434678b310
   lead_key: title:estimating_the_replicability_of_sports_and_exercise_science_research
   queue_status: needs_root_candidate_review
   name: Estimating the Replicability of Sports and Exercise Science Research.
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1007/s40279-025-02201-w
   source_key: PMC12513899 | https://openalex.org/W4411351188
   description: <h4>Background</h4>The replicability of sports and exercise research has not been assessed previously despite concerns about scientific practices within the field.<h4>Aim</h4>This study aims to provide an initial estimate of the replicability of applied sports and exercise science research published in quartile 1 journals (SCImago journal ranking for 2019 in the Sports Science subject category; www.scimagojr.com ) between 2016 and 2021.<h4>Methods</h4>A formalised selection protocol for this replication project was previously published. Voluntary collaborators were recruited, and studies were allocated in a stratified and randomised manner on the basis of equipment and expertise. Original authors were contacted to provide deidentified raw data, to review preregistrations and to provide methodological clarifications. A multiple inferential strategy was employed to analyse the replication data. The same analysis (i.e. F test or t test) was used to determine whether the replication effect size was statistically significant and in the same direction as the original effect size. Z-tests were used to determine whether the original and replication effect size estimates were compatible or significantly different in magnitude.<h4>Results</h4>In total, 25 replication studies were included for analysis. Of the 25, 10 replications used paired t tests, 1 used an independent t test and 14 used an analysis of variance (ANOVA) for the statistical analyses. In all, 7 (28%) studies demonstrated robust replicability, meeting all three validation criteria: achieving statistical significance (p
   current heuristic reason: Matched Figure 1 bibliographic search query '"replication project" "original study" "effect size"'; lead_classification=corpus_database_or_project_signal; score=25; reasons=strong_phrase:replication project | strong_phrase:replication studies | pair_term:original effect | pair_term:replication effect | pair_term:effect size | data_term:data | replication_word | original_word | effect_or_sample_size_phrase | metadata_corpus_signal

27. review_id: review_figure1_search_leads_12b18a2b607a
   lead_key: title:evaluating_meta_analysis_as_a_replication_success_measure
   queue_status: needs_root_candidate_review
   name: Evaluating meta-analysis as a replication success measure.
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1371/journal.pone.0308495
   source_key: PMC11633967
   description: <h4>Background</h4>The importance of replication in the social and behavioural sciences has been emphasized for decades. Various frequentist and Bayesian approaches have been proposed to qualify a replication study as successful or unsuccessful. One of them is meta-analysis. The focus of the present study is on the way meta-analysis functions as a replication success metric. To investigate this, original and replication studies that are part of two large-scale replication projects were used. For each original study, the probability of replication success was calculated using meta-analysis under different assumptions of the underlying population effect when replication results were unknown. The accuracy of the predicted overall replication success was evaluated once replication results became available using adjusted Brier scores.<h4>Results</h4>Our results showed that meta-analysis performed poorly when used as a replication success metric. In many cases, quantifying replication success using meta-analysis resulted in the conclusion where the replication was deemed a success regardless of the results of the replication study.<h4>Discussion</h4>We conclude that when using meta-analysis as a replication success metric, it has a relatively high probability of finding evidence in favour of a non-zero population effect even when it is zero. This behaviour largely results from the significance of the original study. Furthermore, we argue that there are fundamental reasons against using meta-analysis as a metric for replication success.
   current heuristic reason: Matched Figure 1 bibliographic search query '"replication success" "original study"'; lead_classification=corpus_database_or_project_signal; score=23; reasons=strong_phrase:replication project | strong_phrase:large-scale replication | strong_phrase:replication studies | pair_term:original study | replication_word | original_word | metadata_corpus_signal

28. review_id: review_figure1_search_leads_2822063673be
   lead_key: title:evidence_for_goal_and_mixed_evidence_for_false_belief_based_action_prediction_in_2_to_4_year_old_children_a_large_scale_
   queue_status: needs_root_candidate_review
   name: Evidence for goal‐ and mixed evidence for false belief‐based action prediction in 2‐ to 4‐year‐old children: A large‐scale longitudinal anticipatory looking replication study
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1111/desc.13224
   source_key: https://openalex.org/W4200361560
   description: Unsuccessful replication attempts of paradigms assessing children's implicit tracking of false beliefs have instigated the debate on whether or not children have an implicit understanding of false beliefs before the age of four. A novel multi-trial anticipatory looking false belief paradigm yielded evidence of implicit false belief reasoning in 3- to 4-year-old children using a combined score of two false belief conditions (Grosse Wiesmann, C., Friederici, A. D., Singer, T., & Steinbeis, N. [2017]. Developmental Science, 20(5), e12445). The present study is a large-scale replication attempt of this paradigm. The task was administered three times to the same sample of N = 185 children at 2, 3, and 4 years of age. Using the original stimuli, we did not replicate the original finding of above-chance belief-congruent looking in a combined score of two false belief conditions in either of the three age groups. Interestingly, the overall pattern of results was comparable to the original study. Post-hoc analyses revealed, however, that children performed above chance in one false belief condition (FB1) and below chance in the other false belief condition (FB2), thus yielding mixed evidence of children's false belief-based action predictions. Similar to the original study, participants' performance did not change with age and was not related to children's general language skills. This study demonstrates the importance of large-scaled replications and adds to the growing number of research questioning the validity and reliability of anticipatory looking false belief paradigms as a r
   current heuristic reason: Matched Figure 1 bibliographic search query '"large-scale replication" "original study"'; lead_classification=corpus_database_or_project_signal; score=13; reasons=strong_phrase:large-scale replication | pair_term:original study | replication_word | original_word | metadata_corpus_signal

29. review_id: review_figure1_search_leads_3c4dddb6790c
   lead_key: title:evidence_for_infant_directed_speech_preference_is_consistent_across_large_scale_multi_site_replication_and_meta_analysis
   queue_status: needs_root_candidate_review
   name: Evidence for Infant-directed Speech Preference Is Consistent Across Large-scale, Multi-site Replication and Meta-analysis.
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1162/opmi_a_00134
   source_key: PMC11045035
   description: There is substantial evidence that infants prefer infant-directed speech (IDS) to adult-directed speech (ADS). The strongest evidence for this claim has come from two large-scale investigations: i) a community-augmented meta-analysis of published behavioral studies and ii) a large-scale multi-lab replication study. In this paper, we aim to improve our understanding of the IDS preference and its boundary conditions by combining and comparing these two data sources across key population and design characteristics of the underlying studies. Our analyses reveal that both the meta-analysis and multi-lab replication show moderate effect sizes (<i>d</i> ≈ 0.35 for each estimate) and that both of these effects persist when relevant study-level moderators are added to the models (i.e., experimental methods, infant ages, and native languages). However, while the overall effect size estimates were similar, the two sources diverged in the effects of key moderators: both infant age and experimental method predicted IDS preference in the multi-lab replication study, but showed no effect in the meta-analysis. These results demonstrate that the IDS preference generalizes across a variety of experimental conditions and sampling characteristics, while simultaneously identifying key differences in the empirical picture offered by each source individually and pinpointing areas where substantial uncertainty remains about the influence of theoretically central moderators on IDS preference. Overall, our results show how meta-analyses and multi-lab replications can be used in tandem to understand
   current heuristic reason: Matched Figure 1 bibliographic search query '"multi-lab replication" "original study"'; lead_classification=corpus_database_or_project_signal; score=14; reasons=strong_phrase:multi-site replication | pair_term:effect size | data_term:data | replication_word | effect_or_sample_size_phrase | metadata_corpus_signal

30. review_id: review_figure1_search_leads_c7808e6c3826
   lead_key: title:examining_the_replicability_of_online_experiments_selected_by_a_decision_market
   queue_status: needs_root_candidate_review
   name: Examining the replicability of online experiments selected by a decision market.
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1038/s41562-024-02062-9
   source_key: PMC11860227
   description: Here we test the feasibility of using decision markets to select studies for replication and provide evidence about the replicability of online experiments. Social scientists (n = 162) traded on the outcome of close replications of 41 systematically selected MTurk social science experiments published in PNAS 2015-2018, knowing that the 12 studies with the lowest and the 12 with the highest final market prices would be selected for replication, along with 2 randomly selected studies. The replication rate, based on the statistical significance indicator, was 83% for the top-12 and 33% for the bottom-12 group. Overall, 54% of the studies were successfully replicated, with replication effect size estimates averaging 45% of the original effect size estimates. The replication rate varied between 54% and 62% for alternative replication indicators. The observed replicability of MTurk experiments is comparable to that of previous systematic replication projects involving laboratory experiments.
   current heuristic reason: Matched Figure 1 bibliographic search query '"replication project" "original study" "effect size"'; lead_classification=corpus_database_or_project_signal; score=19; reasons=strong_phrase:replication project | pair_term:original effect | pair_term:replication effect | pair_term:effect size | replication_word | original_word | effect_or_sample_size_phrase | metadata_corpus_signal

31. review_id: review_figure1_search_leads_17f20eab2f6e
   lead_key: title:experimental_economics_replication_project
   queue_status: needs_root_candidate_review
   name: Experimental Economics Replication Project
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://osf.io/bzm54/
   source_key: bzm54
   description: We replicate 18 laboratory experimental studies published in two high-impact economics journals in 2011-2014. All replications have a statistical power of ≥90% to detect the original effect size at the 5% significance level.
   current heuristic reason: Matched Figure 1 domain search query 'economics replication project data original study'; lead_classification=corpus_database_or_project_signal; score=17; reasons=strong_phrase:replication project | pair_term:original effect | pair_term:effect size | replication_word | original_word | effect_or_sample_size_phrase | metadata_corpus_signal

32. review_id: review_figure1_search_leads_04919281e4bd
   lead_key: title:fairsharing_record_for_framework_for_open_and_reproducible_research_training_replication_database
   queue_status: needs_root_candidate_review
   name: FAIRsharing record for: Framework for Open and Reproducible Research Training - Replication Database
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://fairsharing.org/10.25504/FAIRsharing.ee7dba
   source_key: 10.25504/fairsharing.ee7dba
   description: This FAIRsharing record describes: FORRT’s Replication Database (FReD) is a community-augmented, quantitative, meta-analytical interface of one of the most comprehensive collections of original and replication findings, including Replications and Reversals and large scale projects such as Many Labs or Registered Replication Reports. Via ReD, students, researchers, and applicants can create summaries of replication findings, search replications, investigate correlates of replicability, and automatically check for replications in reference lists.
   current heuristic reason: Matched Figure 1 repository search query '"replications and reversals" "database"'; lead_classification=corpus_database_or_project_signal; score=27; reasons=strong_phrase:replication database | strong_phrase:registered replication report | strong_phrase:many labs | strong_phrase:replications and reversals | data_term:data | data_term:database | replication_word | original_word | dataset_metadata_surface

33. review_id: review_figure1_search_leads_a5175f329fbc
   lead_key: title:fork_of_reproducibility_project_psychology
   queue_status: needs_root_candidate_review
   name: Fork of Reproducibility Project: Psychology
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://osf.io/wusvb/ | https://osf.io/eq3s2/
   source_key: wusvb | eq3s2
   description: Reproducibility is a defining feature of science, but the extent to which it characterizes current research is unknown. We conducted replications of 100 experimental and correlational studies published in three psychology journals using high-powered designs and original materials when available.
   current heuristic reason: Matched Figure 1 domain search query 'medicine reproducibility project replication dataset effect size'; lead_classification=corpus_database_or_project_signal; score=11; reasons=strong_phrase:reproducibility project | replication_word | original_word | metadata_corpus_signal

34. review_id: review_figure1_search_leads_404c6c8bc341
   lead_key: title:forrt_large_scale_replication_projects_hub
   queue_status: needs_root_candidate_review
   name: FORRT large-scale replication projects hub
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://forrt.org/replication-hub/large-scale-replication-projects/
   source_key: https://forrt.org/replication-hub/large-scale-replication-projects/
   description: Known source-family hub for large-scale replication projects and aliases that can seed Figure 1 corpus/database discovery. Page check: title=List of Large-Scale Replication Projects | FORRT - Framework for Open and Reproducible Research Training; html_bytes=29237; link_count=99
   current heuristic reason: Matched Figure 1 repository search query 'FORRT large-scale replication projects'; lead_classification=corpus_database_or_project_signal; score=15; reasons=strong_phrase:replication project | strong_phrase:large-scale replication | data_term:data | data_term:database | replication_word | query_phrase_in_text

35. review_id: review_figure1_search_leads_4c3314063449
   lead_key: title:forrt_replication_database
   queue_status: needs_root_candidate_review
   name: FORRT Replication Database
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://osf.io/9r62x/
   source_key: 9r62x
   description: Contains materials and data for the FORRT Replication Database
   current heuristic reason: Matched Figure 1 citation search query '"FReD" "Replication Database"'; lead_classification=corpus_database_or_project_signal; score=12; reasons=strong_phrase:replication database | data_term:data | data_term:database | replication_word | repository_data_surface | metadata_corpus_signal

36. review_id: review_figure1_search_leads_fa29ed98a4b6
   lead_key: title:forrt_replication_database_frozen_version_from_08_2024
   queue_status: needs_root_candidate_review
   name: FORRT Replication Database (frozen version from 08/2024)
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://osf.io/c9rny/
   source_key: c9rny
   description: Contains materials and data for the FORRT Replication Database
   current heuristic reason: Matched Figure 1 citation search query '"FReD" "Replication Database"'; lead_classification=corpus_database_or_project_signal; score=12; reasons=strong_phrase:replication database | data_term:data | data_term:database | replication_word | repository_data_surface | metadata_corpus_signal

37. review_id: review_figure1_search_leads_9fabfd38878d
   lead_key: title:forrt_replication_database_fred
   queue_status: needs_root_candidate_review
   name: FORRT Replication Database / FReD
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: reports/corpus_suggestion_tracker.md
   source_key: manual_tracker_row_forrt_replication_database_fred_190c922e4730
   description: Manual suggestion tracker row; status=worked; parser caveats; row=2 | FORRT Replication Database / FReD | worked; parser caveats | Parser now yields 1,969 original-claim rows across 762 original-paper DOI units. Paper-level slope `-0.421`; p<.10 share about 94%. | Not a random journal-paper sample. Rows are original findings selected into replication projects/databases or submitted as replications, so this is a replication-target/focal-claim frame. Not all rows are treatment/intervention effects.
   current heuristic reason: Matched Figure 1 manual search query 'user-suggested replication datasets'; lead_classification=corpus_database_or_project_signal; score=18; reasons=strong_phrase:replication database | strong_phrase:replication project | data_term:data | data_term:database | replication_word | original_word | manual_tracker_status_signal

38. review_id: review_figure1_search_leads_e4909bfbc5b5
   lead_key: title:growth_from_uncertainty_understanding_the_replication_crisis_in_infant_cognition
   queue_status: needs_root_candidate_review
   name: Growth From Uncertainty: Understanding the Replication ‘Crisis’ in Infant Cognition
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1017/psa.2023.157
   source_key: https://openalex.org/W4388716787
   description: Abstract Psychology is a discipline that has a high number of failed replications, which has been characterized as a “crisis” on the assumption that failed replications are indicative of untrustworthy research. This article uses Chang’s concept of epistemic iteration to show how a research program can advance epistemic goals despite many failed replications. It illustrates this by analyzing an ongoing large-scale replication attempt of Southgate et al.’s work exploring infants’ understanding of false beliefs. It concludes that epistemic iteration offers a way of understanding the value of replications—both failed and successful—that contradicts the narrative centered around distrust.
   current heuristic reason: Matched Figure 1 citation search query '"ManyBabies" "replication data"'; lead_classification=corpus_database_or_project_signal; score=9; reasons=strong_phrase:large-scale replication | replication_word | metadata_corpus_signal

39. review_id: review_figure1_search_leads_4267dbece1dc
   lead_key: title:hack_setting_up_a_large_scale_replication_project_of_cognitive_dissonance_theory_beatrix_zone_4_14_45
   queue_status: needs_root_candidate_review
   name: Hack - Setting Up A Large Scale Replication Project of Cognitive Dissonance Theory (Beatrix Zone 4; 14:45)
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://osf.io/294bx/
   source_key: 294bx
   description: 
   current heuristic reason: Matched Figure 1 repository search query '"large-scale replication project" "original study"'; lead_classification=corpus_database_or_project_signal; score=7; reasons=strong_phrase:replication project | replication_word

40. review_id: review_figure1_search_leads_91f39c20a32f
   lead_key: title:heterogeneity_in_direct_replications_in_psychology_and_its_association_with_effect_size
   queue_status: needs_root_candidate_review
   name: Heterogeneity in direct replications in psychology and its association with effect size.
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1037/bul0000294 | https://osf.io/rs7dm/ | https://osf.io/4z3e7/
   source_key: https://openalex.org/W3044062510 | rs7dm | 4z3e7 | 10.1037/bul0000294
   description: We examined the evidence for heterogeneity (of effect sizes) when only minor changes to sample population and settings were made between studies and explored the association between heterogeneity and average effect size in a sample of 68 meta-analyses from 13 preregistered multilab direct replication projects in social and cognitive psychology. Among the many examined effects, examples include the Stroop effect, the "verbal overshadowing" effect, and various priming effects such as "anchoring" effects. We found limited heterogeneity; 48/68 (71%) meta-analyses had nonsignificant heterogeneity, and most (49/68; 72%) were most likely to have zero to small heterogeneity. Power to detect small heterogeneity (as defined by Higgins, Thompson, Deeks, & Altman, 2003) was low for all projects (mean 43%), but good to excellent for medium and large heterogeneity. Our findings thus show little evidence of widespread heterogeneity in direct replication studies in social and cognitive psychology, suggesting that minor changes in sample population and settings are unlikely to affect research outcomes in these fields of psychology. We also found strong correlations between observed average effect sizes (standardized mean differences and log odds ratios) and heterogeneity in our sample. Our results suggest that heterogeneity and moderation of effects is unlikely for a 0 average true effect size, but increasingly likely for larger average true effect size. (PsycInfo Database Record (c) 2020 APA, all rights reserved).
   current heuristic reason: Matched Figure 1 domain search query 'psychology replication database effect size'; lead_classification=corpus_database_or_project_signal; score=20; reasons=strong_phrase:replication project | strong_phrase:replication studies | pair_term:effect size | data_term:data | data_term:database | replication_word | effect_or_sample_size_phrase | metadata_corpus_signal

41. review_id: review_figure1_search_leads_7e275ed173e3
   lead_key: title:how_replicable_are_links_between_personality_traits_and_consequential_life_outcomes_the_life_outcomes_of_personality_rep
   queue_status: needs_root_candidate_review
   name: How Replicable Are Links Between Personality Traits and Consequential Life Outcomes? The Life Outcomes of Personality Replication Project
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1177/0956797619831612
   source_key: https://openalex.org/W2884318343
   description: The Big Five personality traits have been linked to dozens of life outcomes. However, metascientific research has raised questions about the replicability of behavioral science. The Life Outcomes of Personality Replication (LOOPR) Project was therefore conducted to estimate the replicability of the personality-outcome literature. Specifically, I conducted preregistered, high-powered (median N = 1,504) replications of 78 previously published trait-outcome associations. Overall, 87% of the replication attempts were statistically significant in the expected direction. The replication effects were typically 77% as strong as the corresponding original effects, which represents a significant decline in effect size. The replicability of individual effects was predicted by the effect size and design of the original study, as well as the sample size and statistical power of the replication. These results indicate that the personality-outcome literature provides a reasonably accurate map of trait-outcome associations but also that it stands to benefit from efforts to improve replicability.
   current heuristic reason: Matched Figure 1 citation search query '"LOOPR" "replication"'; lead_classification=corpus_database_or_project_signal; score=23; reasons=strong_phrase:replication project | pair_term:original study | pair_term:original effect | pair_term:replication effect | pair_term:effect size | pair_term:sample size | replication_word | original_word | effect_or_sample_size_phrase | metadata_corpus_signal

42. review_id: review_figure1_search_leads_9d2732b5c6ab
   lead_key: title:improving_statistical_analysis_in_team_science_the_case_of_a_bayesian_multiverse_of_many_labs_4
   queue_status: needs_root_candidate_review
   name: Improving Statistical Analysis in Team Science: The Case of a Bayesian Multiverse of Many Labs 4
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.31234/osf.io/cb9er
   source_key: https://openalex.org/W3163808281
   description: Team science projects have become the gold standard for assessing the replicability and variability of key findings in psychological science. However, we believe the typical meta-analytic approach in these projects fails to match the wealth of collected data. Instead, we advocate the use of Bayesian hierarchical modeling for team science projects, potentially extended in a multiverse analysis. We illustrate this full-scale analysis by applying it to the recently published Many Labs 4 project. This project aimed to replicate the mortality salience effect – that being reminded of one’s own death strengthens the own cultural identity. In a multiverse analysis we assess the robustness of the results with varying data inclusion criteria and prior settings. Bayesian model comparison results largely converge to a common conclusion: the data provide evidence against a mortality salience effect across the majority of our analyses. We issue general recommendations to facilitate full-scale analyses in team science projects.
   current heuristic reason: Matched Figure 1 citation search query '"Many Labs" "original study" -> cites:W3163230172'; lead_classification=corpus_database_or_project_signal; score=7; reasons=strong_phrase:many labs | pair_term:full-scale | data_term:data | metadata_corpus_signal | no_replication_language_penalty

43. review_id: review_figure1_search_leads_0cc39d545ae2
   lead_key: title:incidental_attitude_formation_via_the_surveillance_task_a_multi_site_registered_replication_report_of_olson_and_fazio_20
   queue_status: needs_root_candidate_review
   name: Incidental Attitude Formation via the Surveillance Task: A Multi-Site Registered Replication Report of Olson and Fazio (2001) "Implicit Attitude Formation Through Classical Conditioning"
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://osf.io/xqv8b/
   source_key: xqv8b
   description: Measures, researcher instructions, data processing, analysis, and meta-analysis for a Registered Replication Report of Olson &amp; Fazio (2001) to examine the evidence for evaluative conditioning outside of awareness/recollective memory. NB nomenclature has changed over time: despite the title of the original article, "implicit" here refers to self-reported attitudes that were acquired in the absence of awareness/memory of the CS-US pairings, rather than classical conditioning procedures giving rise to implicit attitudes.
   current heuristic reason: Matched Figure 1 repository search query '"registered replication report" data'; lead_classification=corpus_database_or_project_signal; score=11; reasons=strong_phrase:registered replication report | data_term:data | replication_word | original_word | repository_data_surface

44. review_id: review_figure1_search_leads_28438c56840e
   lead_key: title:incorrect_data_in_tables_in_nonvalidation_of_reported_genetic_risk_factors_for_acute_coronary_syndrome_in_a_large_scale_
   queue_status: needs_root_candidate_review
   name: Incorrect Data in Tables in: Nonvalidation of Reported Genetic Risk Factors for Acute Coronary Syndrome in a Large-Scale Replication Study
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1001/jama.298.9.973-b
   source_key: 10.1001/jama.298.9.973-b
   description: 
   current heuristic reason: Matched Figure 1 bibliographic search query '"large-scale replication" "original study"'; lead_classification=corpus_database_or_project_signal; score=10; reasons=strong_phrase:large-scale replication | data_term:data | replication_word | metadata_corpus_signal

45. review_id: review_figure1_search_leads_12655154c792
   lead_key: title:information_bottlenecks_in_behavioural_science_a_framework_and_multi_dataset_analysis_of_replication_and_generalization
   queue_status: needs_root_candidate_review
   name: Information bottlenecks in Behavioural Science: A framework and multi-dataset analysis of replication and generalization
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://osf.io/n67tk/
   source_key: n67tk
   description: The replication crisis has revealed systematic weaknesses in the transmission of scientific knowledge. Here we introduce an information-theoretic framework to quantify how much variability in the world is captured by experiments, retained across replications, and transmitted to a downstream community judgment, operationalized here by direct replication outcomes. We define three measures—Capture, Retention, and Generalizability—based on mutual information between world-level effect sizes, original significance outcomes, and replication outcomes. We apply this approach to four data sets from known replication projects. Results show that only a small fraction of variability in effect sizes is captured by significance testing, and even less is retained in replication. This perspective highlights science as an information-processing system, providing a quantitative account of why the scientific pipeline is so lossy.
   current heuristic reason: Matched Figure 1 domain search query 'management science replication project dataset'; lead_classification=corpus_database_or_project_signal; score=16; reasons=strong_phrase:replication project | pair_term:effect size | data_term:data | data_term:dataset | replication_word | original_word | repository_data_surface | metadata_corpus_signal

46. review_id: review_figure1_search_leads_aa2a7bf31db3
   lead_key: title:investigating_the_replicability_of_preclinical_cancer_biology
   queue_status: needs_root_candidate_review
   name: Investigating the replicability of preclinical cancer biology.
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.7554/elife.71601
   source_key: PMC8651293 | https://openalex.org/W4200247206
   description: Replicability is an important feature of scientific research, but aspects of contemporary research culture, such as an emphasis on novelty, can make replicability seem less important than it should be. The Reproducibility Project: Cancer Biology was set up to provide evidence about the replicability of preclinical research in cancer biology by repeating selected experiments from high-impact papers. A total of 50 experiments from 23 papers were repeated, generating data about the replicability of a total of 158 effects. Most of the original effects were positive effects (136), with the rest being null effects (22). A majority of the original effect sizes were reported as numerical values (117), with the rest being reported as representative images (41). We employed seven methods to assess replicability, and some of these methods were not suitable for all the effects in our sample. One method compared effect sizes: for positive effects, the median effect size in the replications was 85% smaller than the median effect size in the original experiments, and 92% of replication effect sizes were smaller than the original. The other methods were binary - the replication was either a success or a failure - and five of these methods could be used to assess both positive and null effects when effect sizes were reported as numerical values. For positive effects, 40% of replications (39/97) succeeded according to three or more of these five methods, and for null effects 80% of replications (12/15) were successful on this basis; combining positive and null effects, the success rate was 4
   current heuristic reason: Matched Figure 1 bibliographic search query '"replication rates" "coded" "effect sizes"'; lead_classification=corpus_database_or_project_signal; score=20; reasons=strong_phrase:reproducibility project | pair_term:original effect | pair_term:replication effect | pair_term:effect size | data_term:data | replication_word | original_word | effect_or_sample_size_phrase | metadata_corpus_signal

47. review_id: review_figure1_search_leads_564cac4ef29e
   lead_key: title:investigating_variation_in_replicability_a_many_labs_replication_project
   queue_status: needs_root_candidate_review
   name: Investigating Variation in Replicability: A “Many Labs” Replication Project
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.1027/1864-9335/a000178 | https://osf.io/scayl/ | https://osf.io/wx7ck/
   source_key: 10.1027/1864-9335/a000178 | scayl | wx7ck
   description: Semantic Scholar reference neighbor for known corpus/source-family DOI 10.1038/s41562-016-0021.
   current heuristic reason: Matched Figure 1 link_graph search query '10.1038/s41562-016-0021'; lead_classification=corpus_database_or_project_signal; score=17; reasons=strong_phrase:replication project | strong_phrase:many labs | replication_word | known_corpus_paper_link_graph | query_phrase_in_text

48. review_id: review_figure1_search_leads_5cfa0a0e552f
   lead_key: title:linguistic_compression_predicts_replication_failure
   queue_status: needs_root_candidate_review
   name: Linguistic Compression Predicts Replication Failure
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://doi.org/10.17605/osf.io/cpe6f
   source_key: https://openalex.org/W7148330249
   description: This study tests whether linguistic compression in scientific methods sections predicts replication failure. Specifically, it tests whether low temporal conditionality (T-Low: procedures stated without parametric bounds or conditional qualifiers) and low semantic specificity (Sp-Low: categorical rather than parametric descriptions) are higher in papers that failed to replicate than in papers that successfully replicated. The prediction derives from the Conscious Force theoretical framework (Prediction 49): compressed language in methods sections reflects genuine procedural ambiguity — the researcher degrees of freedom that produce non-replicable findings. High-fidelity methods language (specific, conditionally bounded, parametric) reflects procedures specified precisely enough to reproduce. Data source: OSF Reproducibility Project (100 papers), Many Labs 1-3, and the Social Sciences Replication Project (21 papers). Expected N = 150-200 papers with known replication outcomes. All data publicly available. No new data collection required. Design: Archival, single-coder, exploratory pre-registration. Coding has not begun. Replication outcomes are stored separately and will not be merged with coded data until coding is complete.
   current heuristic reason: Matched Figure 1 bibliographic search query '"replication project" "coded data"'; lead_classification=corpus_database_or_project_signal; score=22; reasons=strong_phrase:replication project | strong_phrase:reproducibility project | strong_phrase:many labs | data_term:data | data_term:code | data_term:osf | replication_word | metadata_corpus_signal

49. review_id: review_figure1_search_leads_6e8201e677b6
   lead_key: title:ljcolling_attentional_snarc_v1_0
   queue_status: needs_root_candidate_review
   name: ljcolling/attentional_snarc V1.0
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://zenodo.org/records/3738555
   source_key: 3738555
   description: Repository for Registered Replication Report on Fischer, Castel, Dodd, and Pratt (2003)
   current heuristic reason: Matched Figure 1 repository search query '"registered replication report" "data"'; lead_classification=corpus_database_or_project_signal; score=8; reasons=strong_phrase:registered replication report | data_term:repository | replication_word

50. review_id: review_figure1_search_leads_259d97d285f9
   lead_key: title:management_science_reproducibility_project
   queue_status: needs_root_candidate_review
   name: Management Science Reproducibility Project
   record_kind: candidate_corpus_or_database
   inventory_status: discovered_search_lead
   url: https://osf.io/mjqg5/
   source_key: mjqg5
   description: In the Management Science Reproducibility Project (ManSciReP) we aim to assess the computational reproducibility of studies published in the journal. All papers submitted after June 1, 2019 are subject to code and data review according to the journal’s 2019 Data and Code Disclosure Policy. In this project, we will create a large sample of papers from both before and after the 2019 Data and Code Disclosure Policy took effect. We recruit reviewers (from the Management Science community and outside) who are assigned an article from their own research field, and asked to attempt to reproduce the main results reported in that article. Through a structured survey, reviewers then report back on the extent to which they were able to reproduce the tables, figures, and other main results in the manuscript, and what obstacles they experienced in this endeavor.
   current heuristic reason: Matched Figure 1 domain search query 'management science replication project dataset'; lead_classification=corpus_database_or_project_signal; score=10; reasons=strong_phrase:reproducibility project | data_term:data | data_term:code | repository_data_surface | metadata_corpus_signal

```
