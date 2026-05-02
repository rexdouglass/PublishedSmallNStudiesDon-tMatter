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

```
