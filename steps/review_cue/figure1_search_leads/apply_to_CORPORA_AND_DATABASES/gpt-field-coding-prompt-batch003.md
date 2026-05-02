# GPT Field-Coding Prompt: figure1_search_leads

You are coding rows for `CORPORA_AND_DATABASES.tsv` in a provenance pipeline.
Use web research only to support the requested fields. Do not invent file contents, row counts, column names, or parser status.
If a field requires artifact/file inspection rather than surface metadata, set it to `unknown` and say what must be inspected next.

Return JSON only. The user will save it as `steps/review_cue/figure1_search_leads/apply_to_CORPORA_AND_DATABASES/gpt-field-coding-response-batch003.json`.

JSON shape:

```json
{
  "field_coding_decisions": [
    {
      "coding_task_id": "...",
      "lead_key": "...",
      "field_values": {
        "source_family": "...",
        "domain_or_field": "...",
        "description": "...",
        "why_relevant": "...",
        "result_fields_available": "...",
        "has_d_or_convertible_effect": "...",
        "has_n": "...",
        "has_replication_pair_mapping": "...",
        "has_publication_links": "...",
        "parser_family": "...",
        "blocker_codes": "...",
        "next_action": "...",
        "notes": "..."
      },
      "field_basis": {
        "source_family": "short evidence basis or unknown rationale",
        "domain_or_field": "short evidence basis or unknown rationale",
        "description": "short evidence basis or unknown rationale",
        "why_relevant": "short evidence basis or unknown rationale",
        "result_fields_available": "short evidence basis or unknown rationale",
        "has_d_or_convertible_effect": "short evidence basis or unknown rationale",
        "has_n": "short evidence basis or unknown rationale",
        "has_replication_pair_mapping": "short evidence basis or unknown rationale",
        "has_publication_links": "short evidence basis or unknown rationale",
        "parser_family": "short evidence basis or unknown rationale",
        "blocker_codes": "short evidence basis or unknown rationale",
        "next_action": "short evidence basis or unknown rationale",
        "notes": "short evidence basis or unknown rationale"
      },
      "field_confidence": {
        "source_family": "high|medium|low",
        "domain_or_field": "high|medium|low",
        "description": "high|medium|low",
        "why_relevant": "high|medium|low",
        "result_fields_available": "high|medium|low",
        "has_d_or_convertible_effect": "high|medium|low",
        "has_n": "high|medium|low",
        "has_replication_pair_mapping": "high|medium|low",
        "has_publication_links": "high|medium|low",
        "parser_family": "high|medium|low",
        "blocker_codes": "high|medium|low",
        "next_action": "high|medium|low",
        "notes": "high|medium|low"
      },
      "sources_checked": [
        "URL or file path"
      ]
    }
  ]
}
```

Allowed yes/no fields must use `yes`, `no`, or `unknown`: `has_d_or_convertible_effect`, `has_n`, `has_replication_pair_mapping`, `has_publication_links`.

Rows to code:

## 1. A large-scale replication of scenario-based experiments in psychology and management using large language models
- coding_task_id: `fieldcode_title_a_large_scale_replication_of_scenario_based_experiments_in_psychology_and_management_using_large_language_models`
- lead_key: `title:a_large_scale_replication_of_scenario_based_experiments_in_psychology_and_management_using_large_language_models`
- landing_url: `https://doi.org/10.1038/s43588-025-00840-7`
- source_key: `10.1038/s43588-025-00840-7 | doi:10.1038/s43588-025-00840-7`
- fields_to_code: `domain_or_field | description | why_relevant | has_d_or_convertible_effect | has_n | has_replication_pair_mapping | parser_family`

Evidence packet:

```json
{
  "current_description": "",
  "current_notes": "provider=crossref | external_id=10.1038/s43588-025-00840-7 | doi=10.1038/s43588-025-00840-7 | review_cue=figure1_search_leads | decision=keep_in_corpora_and_databases | confidence=medium | reason=The Nature Computational Science article title identifies a large-scale replication of scenario-based experiments. It is plausibly a multi-study source-family candidate, but source inventory must confirm whether article data or supplements expose original/replication mapping and usable result fields.",
  "current_why_relevant": "Matched Figure 1 bibliographic search query '\"large-scale replication\" \"dataset\"'; lead_classification=corpus_database_or_project_signal; score=9; reasons=strong_phrase:large-scale replication | replication_word | metadata_corpus_signal",
  "decision": "keep_in_corpora_and_databases",
  "landing_url": "https://doi.org/10.1038/s43588-025-00840-7",
  "lead_key": "title:a_large_scale_replication_of_scenario_based_experiments_in_psychology_and_management_using_large_language_models",
  "name": "A large-scale replication of scenario-based experiments in psychology and management using large language models",
  "proposal_basis": "The Nature Computational Science article title identifies a large-scale replication of scenario-based experiments. It is plausibly a multi-study source-family candidate, but source inventory must confirm whether article data or supplements expose original/replication mapping and usable result fields.",
  "source_key": "10.1038/s43588-025-00840-7 | doi:10.1038/s43588-025-00840-7"
}
```

## 2. A multi-site Registered Replication Report of Olson &amp; Fazio (2001) "Implicit Attitude Formation Through Classical Conditioning"
- coding_task_id: `fieldcode_title_a_multi_site_registered_replication_report_of_olson_amp_fazio_2001_implicit_attitude_formation_through_classical_conditi`
- lead_key: `title:a_multi_site_registered_replication_report_of_olson_amp_fazio_2001_implicit_attitude_formation_through_classical_conditi`
- landing_url: `https://osf.io/3hjpf/`
- source_key: `3hjpf`
- fields_to_code: `domain_or_field | why_relevant | has_d_or_convertible_effect | has_n | has_replication_pair_mapping | has_publication_links | parser_family`

Evidence packet:

```json
{
  "current_description": "NB nomenclature has changed over time: despite title of original article, \"implicit\" here refers to self-reported attitudes that were acquired in the absence of awareness/memory of the CS-US pairings (rather than classical conditioning procedures giving rise to implicit attitudes)",
  "current_notes": "provider=osf | external_id=3hjpf | doi= | review_cue=figure1_search_leads | decision=keep_in_corpora_and_databases | confidence=high | reason=The stale OSF 3hjpf lead is the Olson and Fazio registered replication source family | the canonical public project is OSF hs32y and the article DOI is 10.1177/0956797620968526. It should be kept but deduplicated to that canonical route.",
  "current_why_relevant": "Matched Figure 1 repository search query '\"registered replication report\" data'; lead_classification=corpus_database_or_project_signal; score=9; reasons=strong_phrase:registered replication report | replication_word | original_word",
  "decision": "keep_in_corpora_and_databases",
  "landing_url": "https://osf.io/3hjpf/",
  "lead_key": "title:a_multi_site_registered_replication_report_of_olson_amp_fazio_2001_implicit_attitude_formation_through_classical_conditi",
  "name": "A multi-site Registered Replication Report of Olson &amp; Fazio (2001) \"Implicit Attitude Formation Through Classical Conditioning\"",
  "proposal_basis": "The stale OSF 3hjpf lead is the Olson and Fazio registered replication source family; the canonical public project is OSF hs32y and the article DOI is 10.1177/0956797620968526. It should be kept but deduplicated to that canonical route.",
  "source_key": "3hjpf"
}
```

## 3. A Multilab Preregistered Replication of the Ego-Depletion Effect
- coding_task_id: `fieldcode_title_a_multilab_preregistered_replication_of_the_ego_depletion_effect`
- lead_key: `title:a_multilab_preregistered_replication_of_the_ego_depletion_effect`
- landing_url: `https://doi.org/10.1177/1745691616652873`
- source_key: `https://openalex.org/W2499154041 | doi:10.1177/1745691616652873`
- fields_to_code: `domain_or_field | why_relevant | has_d_or_convertible_effect | has_replication_pair_mapping | parser_family`

Evidence packet:

```json
{
  "current_description": "Good self-control has been linked to adaptive outcomes such as better health, cohesive personal relationships, success in the workplace and at school, and less susceptibility to crime and addictions. In contrast, self-control failure is linked to maladaptive outcomes. Understanding the mechanisms by which self-control predicts behavior may assist in promoting better regulation and outcomes. A popular approach to understanding self-control is the strength or resource depletion model. Self-control is conceptualized as a limited resource that becomes depleted after a period of exertion resulting in self-control failure. The model has typically been tested using a sequential-task experimental paradigm, in which people completing an initial self-control task have reduced self-control capacity and poorer performance on a subsequent task, a state known as ego depletion Although a meta-analysis of ego-depletion experiments found a medium-sized effect, subsequent meta-analyses have questioned the size and existence of the effect and identified instances of possible bias. The analyses served as a catalyst for the current Registered Replication Report of the ego-depletion effect. Multiple laboratories (k = 23, total N = 2,141) conducted replications of a standardized ego-depletion protocol based on a sequential-task paradigm by Sripada et al. Meta-analysis of the studies revealed that the size of the ego-depletion effect was small with 95% confidence intervals (CIs) that encompassed zero (d = 0.04, 95% CI [-0.07, 0.15]. We discuss implications of the findings for the ego-depletion eff",
  "current_notes": "provider=openalex | external_id=https://openalex.org/W2499154041 | doi=https://doi.org/10.1177/1745691616652873 | review_cue=figure1_search_leads | decision=keep_in_corpora_and_databases | confidence=high | reason=This Registered Replication Report is a multi-lab source-family candidate: the abstract reports 23 laboratories and N=2141 for a standardized ego-depletion replication protocol. It should stay for source inventory and table extraction review.",
  "current_why_relevant": "Matched Figure 1 citation search query '\"registered replication report\" \"many labs\"'; lead_classification=corpus_database_or_project_signal; score=7; reasons=strong_phrase:registered replication report | replication_word",
  "decision": "keep_in_corpora_and_databases",
  "landing_url": "https://doi.org/10.1177/1745691616652873",
  "lead_key": "title:a_multilab_preregistered_replication_of_the_ego_depletion_effect",
  "name": "A Multilab Preregistered Replication of the Ego-Depletion Effect",
  "proposal_basis": "This Registered Replication Report is a multi-lab source-family candidate: the abstract reports 23 laboratories and N=2141 for a standardized ego-depletion replication protocol. It should stay for source inventory and table extraction review.",
  "source_key": "https://openalex.org/W2499154041 | doi:10.1177/1745691616652873"
}
```

## 4. An open investigation of the reproducibility of cancer biology research
- coding_task_id: `fieldcode_title_an_open_investigation_of_the_reproducibility_of_cancer_biology_research`
- lead_key: `title:an_open_investigation_of_the_reproducibility_of_cancer_biology_research`
- landing_url: `https://doi.org/10.7554/elife.04333`
- source_key: `https://openalex.org/W2142148275 | rpcb | doi:10.7554/elife.04333`
- fields_to_code: `domain_or_field | why_relevant | has_d_or_convertible_effect | has_n | has_replication_pair_mapping | parser_family`

Evidence packet:

```json
{
  "current_description": "It is widely believed that research that builds upon previously published findings has reproduced the original work. However, it is rare for researchers to perform or publish direct replications of existing results. The Reproducibility Project: Cancer Biology is an open investigation of reproducibility in preclinical cancer biology research. We have identified 50 high impact cancer biology articles published in the period 2010-2012, and plan to replicate a subset of experimental results from each article. A Registered Report detailing the proposed experimental designs and protocols for each subset of experiments will be peer reviewed and published prior to data collection. The results of these experiments will then be published in a Replication Study. The resulting open methodology and dataset will provide evidence about the reproducibility of high-impact results, and an opportunity to identify predictors of reproducibility.",
  "current_notes": "provider=openalex | external_id=https://openalex.org/W2142148275 | doi=https://doi.org/10.7554/elife.04333 | review_cue=figure1_search_leads | decision=keep_in_corpora_and_databases | confidence=high | reason=This eLife article defines the Reproducibility Project: Cancer Biology source family, identifying 50 high-impact cancer biology articles and planned replication studies. It should be retained but deduplicated with the later RPCB result-data source-family records.",
  "current_why_relevant": "Matched Figure 1 citation search query '\"Reproducibility Project: Psychology\" dataset replication'; lead_classification=corpus_database_or_project_signal; score=13; reasons=strong_phrase:reproducibility project | data_term:data | data_term:dataset | replication_word | original_word | metadata_corpus_signal",
  "decision": "keep_in_corpora_and_databases",
  "landing_url": "https://doi.org/10.7554/elife.04333",
  "lead_key": "title:an_open_investigation_of_the_reproducibility_of_cancer_biology_research",
  "name": "An open investigation of the reproducibility of cancer biology research",
  "proposal_basis": "This eLife article defines the Reproducibility Project: Cancer Biology source family, identifying 50 high-impact cancer biology articles and planned replication studies. It should be retained but deduplicated with the later RPCB result-data source-family records.",
  "source_key": "https://openalex.org/W2142148275 | rpcb | doi:10.7554/elife.04333"
}
```

## 5. Comparing Meta Analyses And Pre Registered Multiple Labs Replication Projects
- coding_task_id: `fieldcode_title_comparing_meta_analyses_and_pre_registered_multiple_labs_replication_projects`
- lead_key: `title:comparing_meta_analyses_and_pre_registered_multiple_labs_replication_projects`
- landing_url: ``
- source_key: `10.31219/osf.io/brzwt`
- fields_to_code: `source_family | domain_or_field | description | result_fields_available | has_d_or_convertible_effect | has_n | has_replication_pair_mapping | has_publication_links | parser_family`

Evidence packet:

```json
{
  "current_description": "",
  "current_notes": "review_cue=figure1_search_leads | decision=keep_in_corpora_and_databases | confidence=medium | reason=The preprint describes a reusable multi-row comparison of 17 meta-analyses with matching multiple-labs replication projects, including meta-analytic and replication effect sizes. It should be inventoried as a candidate source-family/table source before extraction.",
  "current_why_relevant": "The preprint describes a reusable multi-row comparison of 17 meta-analyses with matching multiple-labs replication projects, including meta-analytic and replication effect sizes. It should be inventoried as a candidate source-family/table source before extraction.",
  "decision": "keep_in_corpora_and_databases",
  "landing_url": "",
  "lead_key": "title:comparing_meta_analyses_and_pre_registered_multiple_labs_replication_projects",
  "name": "Comparing Meta Analyses And Pre Registered Multiple Labs Replication Projects",
  "proposal_basis": "The preprint describes a reusable multi-row comparison of 17 meta-analyses with matching multiple-labs replication projects, including meta-analytic and replication effect sizes. It should be inventoried as a candidate source-family/table source before extraction.",
  "source_key": "10.31219/osf.io/brzwt"
}
```

## 6. Compilation Of Diener Et Al 2010 Osf Multi Site Replication Projects
- coding_task_id: `fieldcode_title_compilation_of_diener_et_al_2010_osf_multi_site_replication_projects`
- lead_key: `title:compilation_of_diener_et_al_2010_osf_multi_site_replication_projects`
- landing_url: ``
- source_key: `qdx7p`
- fields_to_code: `source_family | domain_or_field | description | result_fields_available | has_d_or_convertible_effect | has_n | has_replication_pair_mapping | has_publication_links | parser_family`

Evidence packet:

```json
{
  "current_description": "",
  "current_notes": "review_cue=figure1_search_leads | decision=keep_in_corpora_and_databases | confidence=high | reason=The OSF page is a source-family/data package compiling Diener et al. (2010) multi-site replication datasets and analysis materials. It should be inventoried for reusable original/replication result tables.",
  "current_why_relevant": "The OSF page is a source-family/data package compiling Diener et al. (2010) multi-site replication datasets and analysis materials. It should be inventoried for reusable original/replication result tables.",
  "decision": "keep_in_corpora_and_databases",
  "landing_url": "",
  "lead_key": "title:compilation_of_diener_et_al_2010_osf_multi_site_replication_projects",
  "name": "Compilation Of Diener Et Al 2010 Osf Multi Site Replication Projects",
  "proposal_basis": "The OSF page is a source-family/data package compiling Diener et al. (2010) multi-site replication datasets and analysis materials. It should be inventoried for reusable original/replication result tables.",
  "source_key": "qdx7p"
}
```

## 7. Data from Investigating Variation in Replicability: A “Many Labs” Replication Project
- coding_task_id: `fieldcode_title_data_from_investigating_variation_in_replicability_a_many_labs_replication_project`
- lead_key: `title:data_from_investigating_variation_in_replicability_a_many_labs_replication_project`
- landing_url: `https://doi.org/10.5334/jopd.ad | https://doi.org/10.31234/osf.io/25ju4`
- source_key: `https://openalex.org/W2126632863 | https://openalex.org/W4226251881 | 10.5334/jopd.ad`
- fields_to_code: `domain_or_field | why_relevant | has_d_or_convertible_effect | has_replication_pair_mapping | parser_family`

Evidence packet:

```json
{
  "current_description": "<p class=\"p1\">This dataset is from the Many Labs Replication Project in which 13 effects were replicated across 36 samples and over 6,000 participants. Data from the replications are included, along with demographic variables about the participants and contextual information about the environment in which the replication was conducted. Data were collected in-lab and online through a standardized procedure administered via an online link. The dataset is stored on the Open Science Framework website. These data could be used to further investigate the results of the included 13 effects or to study replication and generalizability more broadly.",
  "current_notes": "provider=openalex | external_id=https://openalex.org/W2126632863 | doi=https://doi.org/10.5334/jopd.ad | external_id=https://openalex.org/W4226251881 | doi=https://doi.org/10.31234/osf.io/25ju4 | provider=crossref | external_id=10.5334/jopd.ad | doi=10.5334/jopd.ad | review_cue=figure1_search_leads | decision=keep_in_corpora_and_databases | confidence=high | reason=This Journal of Open Psychology Data article is the data source for the Many Labs replication project and should be retained as a source-family/data-package candidate.",
  "current_why_relevant": "Matched Figure 1 citation search query '\"Many Labs\" replication project dataset'; lead_classification=corpus_database_or_project_signal; score=16; reasons=strong_phrase:replication project | strong_phrase:many labs | data_term:data | data_term:dataset | replication_word | metadata_corpus_signal",
  "decision": "keep_in_corpora_and_databases",
  "landing_url": "https://doi.org/10.5334/jopd.ad | https://doi.org/10.31234/osf.io/25ju4",
  "lead_key": "title:data_from_investigating_variation_in_replicability_a_many_labs_replication_project",
  "name": "Data from Investigating Variation in Replicability: A \u201cMany Labs\u201d Replication Project",
  "proposal_basis": "This Journal of Open Psychology Data article is the data source for the Many Labs replication project and should be retained as a source-family/data-package candidate.",
  "source_key": "https://openalex.org/W2126632863 | https://openalex.org/W4226251881 | 10.5334/jopd.ad"
}
```

## 8. Eleven years of student replication projects provide evidence on the correlates of replicability in psychology.
- coding_task_id: `fieldcode_title_eleven_years_of_student_replication_projects_provide_evidence_on_the_correlates_of_replicability_in_psychology`
- lead_key: `title:eleven_years_of_student_replication_projects_provide_evidence_on_the_correlates_of_replicability_in_psychology`
- landing_url: `https://doi.org/10.1098/rsos.231240`
- source_key: `PMC10645069 | 10.1098/rsos.231240`
- fields_to_code: `domain_or_field | why_relevant | parser_family`

Evidence packet:

```json
{
  "current_description": "Cumulative scientific progress requires empirical results that are robust enough to support theory construction and extension. Yet in psychology, some prominent findings have failed to replicate, and large-scale studies suggest replicability issues are widespread. The identification of predictors of replication success is limited by the difficulty of conducting large samples of independent replication experiments, however: most investigations reanalyse the same set of 170 replications. We introduce a new dataset of 176 replications from students in a graduate-level methods course. Replication results were judged to be successful in 49% of replications; of the 136 where effect sizes could be numerically compared, 46% had point estimates within the prediction interval of the original outcome (versus the expected 95%). Larger original effect sizes and within-participants designs were especially related to replication success. Our results indicate that, consistent with prior reports, the robustness of the psychology literature is low enough to limit cumulative progress by student investigators.",
  "current_notes": "provider=europepmc | external_id=PMC10645069 | doi=10.1098/rsos.231240 | review_cue=figure1_search_leads | decision=keep_in_corpora_and_databases | confidence=high | reason=The article introduces a new dataset of 176 student replications, including comparable effect-size information for many rows. This is a reusable corpus/source-family candidate for Figure 1 inventory.",
  "current_why_relevant": "Matched Figure 1 bibliographic search query '\"replication rates\" \"coded\" \"effect sizes\"'; lead_classification=corpus_database_or_project_signal; score=17; reasons=strong_phrase:replication project | pair_term:original effect | pair_term:effect size | data_term:data | data_term:dataset | replication_word | original_word | metadata_corpus_signal",
  "decision": "keep_in_corpora_and_databases",
  "landing_url": "https://doi.org/10.1098/rsos.231240",
  "lead_key": "title:eleven_years_of_student_replication_projects_provide_evidence_on_the_correlates_of_replicability_in_psychology",
  "name": "Eleven years of student replication projects provide evidence on the correlates of replicability in psychology.",
  "proposal_basis": "The article introduces a new dataset of 176 student replications, including comparable effect-size information for many rows. This is a reusable corpus/source-family candidate for Figure 1 inventory.",
  "source_key": "PMC10645069 | 10.1098/rsos.231240"
}
```

## 9. Estimating the Replicability of Sports and Exercise Science Research.
- coding_task_id: `fieldcode_title_estimating_the_replicability_of_sports_and_exercise_science_research`
- lead_key: `title:estimating_the_replicability_of_sports_and_exercise_science_research`
- landing_url: `https://doi.org/10.1007/s40279-025-02201-w`
- source_key: `PMC12513899 | 10.1007/s40279-025-02201-w`
- fields_to_code: `domain_or_field | why_relevant | has_n | parser_family`

Evidence packet:

```json
{
  "current_description": "<h4>Background</h4>The replicability of sports and exercise research has not been assessed previously despite concerns about scientific practices within the field.<h4>Aim</h4>This study aims to provide an initial estimate of the replicability of applied sports and exercise science research published in quartile 1 journals (SCImago journal ranking for 2019 in the Sports Science subject category; www.scimagojr.com ) between 2016 and 2021.<h4>Methods</h4>A formalised selection protocol for this replication project was previously published. Voluntary collaborators were recruited, and studies were allocated in a stratified and randomised manner on the basis of equipment and expertise. Original authors were contacted to provide deidentified raw data, to review preregistrations and to provide methodological clarifications. A multiple inferential strategy was employed to analyse the replication data. The same analysis (i.e. F test or t test) was used to determine whether the replication effect size was statistically significant and in the same direction as the original effect size. Z-tests were used to determine whether the original and replication effect size estimates were compatible or significantly different in magnitude.<h4>Results</h4>In total, 25 replication studies were included for analysis. Of the 25, 10 replications used paired t tests, 1 used an independent t test and 14 used an analysis of variance (ANOVA) for the statistical analyses. In all, 7 (28%) studies demonstrated robust replicability, meeting all three validation criteria: achieving statistical significance (p",
  "current_notes": "provider=europepmc | external_id=PMC12513899 | doi=10.1007/s40279-025-02201-w | review_cue=figure1_search_leads | decision=keep_in_corpora_and_databases | confidence=high | reason=This is the Sports Science Replication Centre result article, reporting 25 replication studies with original and replication effect-size comparisons. It is a high-value source-family candidate.",
  "current_why_relevant": "Matched Figure 1 bibliographic search query '\"replication project\" \"sample size\" \"effect size\"'; lead_classification=corpus_database_or_project_signal; score=25; reasons=strong_phrase:replication project | strong_phrase:replication studies | pair_term:original effect | pair_term:replication effect | pair_term:effect size | data_term:data | replication_word | original_word | effect_or_sample_size_phrase | metadata_corpus_signal",
  "decision": "keep_in_corpora_and_databases",
  "landing_url": "https://doi.org/10.1007/s40279-025-02201-w",
  "lead_key": "title:estimating_the_replicability_of_sports_and_exercise_science_research",
  "name": "Estimating the Replicability of Sports and Exercise Science Research.",
  "proposal_basis": "This is the Sports Science Replication Centre result article, reporting 25 replication studies with original and replication effect-size comparisons. It is a high-value source-family candidate.",
  "source_key": "PMC12513899 | 10.1007/s40279-025-02201-w"
}
```

## 10. Examining the replicability of online experiments selected by a decision market.
- coding_task_id: `fieldcode_title_examining_the_replicability_of_online_experiments_selected_by_a_decision_market`
- lead_key: `title:examining_the_replicability_of_online_experiments_selected_by_a_decision_market`
- landing_url: `https://doi.org/10.1038/s41562-024-02062-9`
- source_key: `PMC11860227 | 10.1038/s41562-024-02062-9`
- fields_to_code: `domain_or_field | why_relevant | has_n | parser_family`

Evidence packet:

```json
{
  "current_description": "Here we test the feasibility of using decision markets to select studies for replication and provide evidence about the replicability of online experiments. Social scientists (n = 162) traded on the outcome of close replications of 41 systematically selected MTurk social science experiments published in PNAS 2015-2018, knowing that the 12 studies with the lowest and the 12 with the highest final market prices would be selected for replication, along with 2 randomly selected studies. The replication rate, based on the statistical significance indicator, was 83% for the top-12 and 33% for the bottom-12 group. Overall, 54% of the studies were successfully replicated, with replication effect size estimates averaging 45% of the original effect size estimates. The replication rate varied between 54% and 62% for alternative replication indicators. The observed replicability of MTurk experiments is comparable to that of previous systematic replication projects involving laboratory experiments.",
  "current_notes": "provider=europepmc | external_id=PMC11860227 | doi=10.1038/s41562-024-02062-9 | review_cue=figure1_search_leads | decision=keep_in_corpora_and_databases | confidence=high | reason=This is a systematic replication source family: 41 MTurk experiments were candidates, 26 were selected for replication, and the article reports original/replication effect-size relationships. It already has routed result-table child artifacts.",
  "current_why_relevant": "Matched Figure 1 bibliographic search query '\"original and replication\" \"effect size\" \"sample size\"'; lead_classification=corpus_database_or_project_signal; score=19; reasons=strong_phrase:replication project | pair_term:original effect | pair_term:replication effect | pair_term:effect size | replication_word | original_word | effect_or_sample_size_phrase | metadata_corpus_signal",
  "decision": "keep_in_corpora_and_databases",
  "landing_url": "https://doi.org/10.1038/s41562-024-02062-9",
  "lead_key": "title:examining_the_replicability_of_online_experiments_selected_by_a_decision_market",
  "name": "Examining the replicability of online experiments selected by a decision market.",
  "proposal_basis": "This is a systematic replication source family: 41 MTurk experiments were candidates, 26 were selected for replication, and the article reports original/replication effect-size relationships. It already has routed result-table child artifacts.",
  "source_key": "PMC11860227 | 10.1038/s41562-024-02062-9"
}
```

## 11. Experimental Economics Replication Project
- coding_task_id: `fieldcode_title_experimental_economics_replication_project`
- lead_key: `title:experimental_economics_replication_project`
- landing_url: `https://osf.io/bzm54/`
- source_key: `bzm54`
- fields_to_code: `domain_or_field | why_relevant | has_n | has_publication_links | parser_family`

Evidence packet:

```json
{
  "current_description": "We replicate 18 laboratory experimental studies published in two high-impact economics journals in 2011-2014. All replications have a statistical power of \u226590% to detect the original effect size at the 5% significance level.",
  "current_notes": "provider=osf | external_id=bzm54 | doi= | review_cue=figure1_search_leads | decision=keep_in_corpora_and_databases | confidence=high | reason=This is the Experimental Economics Replication Project source-family lead, describing replications of 18 laboratory experimental studies with high powered designs. It belongs in source-family inventory and should be deduplicated to the canonical website/OSF route already identified.",
  "current_why_relevant": "Matched Figure 1 domain search query 'economics replication project original estimates'; lead_classification=corpus_database_or_project_signal; score=17; reasons=strong_phrase:replication project | pair_term:original effect | pair_term:effect size | replication_word | original_word | effect_or_sample_size_phrase | metadata_corpus_signal",
  "decision": "keep_in_corpora_and_databases",
  "landing_url": "https://osf.io/bzm54/",
  "lead_key": "title:experimental_economics_replication_project",
  "name": "Experimental Economics Replication Project",
  "proposal_basis": "This is the Experimental Economics Replication Project source-family lead, describing replications of 18 laboratory experimental studies with high powered designs. It belongs in source-family inventory and should be deduplicated to the canonical website/OSF route already identified.",
  "source_key": "bzm54"
}
```

## 12. Forrt Large Scale Replication Projects Hub
- coding_task_id: `fieldcode_title_forrt_large_scale_replication_projects_hub`
- lead_key: `title:forrt_large_scale_replication_projects_hub`
- landing_url: ``
- source_key: `https://forrt.org/replication-hub/large-scale-replication-projects/`
- fields_to_code: `source_family | domain_or_field | description | result_fields_available | has_d_or_convertible_effect | has_n | has_replication_pair_mapping | has_publication_links | parser_family`

Evidence packet:

```json
{
  "current_description": "",
  "current_notes": "review_cue=figure1_search_leads | decision=keep_in_corpora_and_databases | confidence=high | reason=The FORRT large-scale replication projects page is a reusable source-family hub for identifying replication projects and aliases. It should be kept as a discovery/inventory source, while individual project rows still need artifact-level validation.",
  "current_why_relevant": "The FORRT large-scale replication projects page is a reusable source-family hub for identifying replication projects and aliases. It should be kept as a discovery/inventory source, while individual project rows still need artifact-level validation.",
  "decision": "keep_in_corpora_and_databases",
  "landing_url": "",
  "lead_key": "title:forrt_large_scale_replication_projects_hub",
  "name": "Forrt Large Scale Replication Projects Hub",
  "proposal_basis": "The FORRT large-scale replication projects page is a reusable source-family hub for identifying replication projects and aliases. It should be kept as a discovery/inventory source, while individual project rows still need artifact-level validation.",
  "source_key": "https://forrt.org/replication-hub/large-scale-replication-projects/"
}
```

## 13. FReD current snapshot diff
- coding_task_id: `fieldcode_title_forrt_replication_database`
- lead_key: `title:forrt_replication_database`
- landing_url: `https://osf.io/9r62x/`
- source_key: `fred_diff_2024 | 9r62x`
- fields_to_code: `domain_or_field | description | has_n | has_publication_links`

Evidence packet:

```json
{
  "current_description": "",
  "current_notes": "Diff only source never bulk re-ingest | review_cue=figure1_search_leads | decision=keep_in_corpora_and_databases | confidence=high | reason=The OSF node explicitly contains materials and data for the FORRT Replication Database/FReD, a major source of original and replication findings. It belongs in source-family inventory.",
  "current_why_relevant": "Diff only source never bulk re-ingest",
  "decision": "keep_in_corpora_and_databases",
  "landing_url": "https://osf.io/9r62x/",
  "lead_key": "title:forrt_replication_database",
  "name": "FReD current snapshot diff",
  "proposal_basis": "The OSF node explicitly contains materials and data for the FORRT Replication Database/FReD, a major source of original and replication findings. It belongs in source-family inventory.",
  "source_key": "fred_diff_2024 | 9r62x"
}
```

## 14. Reproducibility Project - Psychology: Design
- coding_task_id: `fieldcode_title_reproducibility_project_psychology_design`
- lead_key: `title:reproducibility_project_psychology_design`
- landing_url: `https://osf.io/i68pe/`
- source_key: `i68pe | osf:i68pe`
- fields_to_code: `domain_or_field | description | why_relevant | has_d_or_convertible_effect | has_n | has_replication_pair_mapping | has_publication_links | parser_family`

Evidence packet:

```json
{
  "current_description": "",
  "current_notes": "provider=osf | external_id=i68pe | doi= | review_cue=figure1_search_leads | decision=keep_in_corpora_and_databases | confidence=high | reason=This is a real Reproducibility Project: Psychology OSF project/source-family lead. It belongs in the root corpus/database inventory because it can expose multiple original/replication pair rows after file-level inventory.",
  "current_why_relevant": "Matched Figure 1 repository search query '\"Reproducibility Project\" coded data'; lead_classification=corpus_database_or_project_signal; score=5; reasons=strong_phrase:reproducibility project",
  "decision": "keep_in_corpora_and_databases",
  "landing_url": "https://osf.io/i68pe/",
  "lead_key": "title:reproducibility_project_psychology_design",
  "name": "Reproducibility Project - Psychology: Design",
  "proposal_basis": "This is a real Reproducibility Project: Psychology OSF project/source-family lead. It belongs in the root corpus/database inventory because it can expose multiple original/replication pair rows after file-level inventory.",
  "source_key": "i68pe | osf:i68pe"
}
```

## 15. Rescience C Contents
- coding_task_id: `fieldcode_title_rescience_c_contents`
- lead_key: `title:rescience_c_contents`
- landing_url: ``
- source_key: `https://rescience.github.io/read/`
- fields_to_code: `source_family | domain_or_field | description | result_fields_available | has_d_or_convertible_effect | has_n | has_replication_pair_mapping | has_publication_links | parser_family`

Evidence packet:

```json
{
  "current_description": "",
  "current_notes": "review_cue=figure1_search_leads | decision=promote_to_corpora_and_databases | confidence=high | reason=ReScience C is a journal/source-family contents page for computational replication articles, with many article records and code/review metadata. It is a reusable source-family object rather than a single paper.",
  "current_why_relevant": "ReScience C is a journal/source-family contents page for computational replication articles, with many article records and code/review metadata. It is a reusable source-family object rather than a single paper.",
  "decision": "promote_to_corpora_and_databases",
  "landing_url": "",
  "lead_key": "title:rescience_c_contents",
  "name": "Rescience C Contents",
  "proposal_basis": "ReScience C is a journal/source-family contents page for computational replication articles, with many article records and code/review metadata. It is a reusable source-family object rather than a single paper.",
  "source_key": "https://rescience.github.io/read/"
}
```
