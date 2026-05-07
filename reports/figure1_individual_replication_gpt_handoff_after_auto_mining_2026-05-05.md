# GPT Handoff: Individual Replication Papers After Automatic Mining

We are building Figure 1 rows at the paper-pair/study-outcome level. Automatic local mining has already promoted every row it could support from mirrored value-bearing source text. The remaining rows below need outside search, exact source-object acquisition, or judgment about whether the design/outcome can be mapped to Figure 1.

Current local counts:
- Figure 1 plotted table rows: 2,456
- Promoted individual-replication rows: 25
- Handoff candidates in this packet: 35
- Priority distribution: {'1': 7, '2': 28}

Important rules:
- Do not infer values from vibes or from a citation alone.
- A usable Figure 1 row needs a specific original result mapped to a specific replication/follow-up result, original N, replication N, original effect, replication effect, and a defensible D/SMD or D-equivalent conversion route.
- If the source only supports a native regression, interaction, survival, genetics, psychometric, or one-arm result, return `native_only` unless a concrete conversion is justified.
- If a source object is blocked or the exact original/replication outcome is ambiguous, return `needs_more_evidence` with the next source to acquire.
- Preserve verbatim source text for effect, N, relationship, outcome selector, and conversion inputs.

Return strict JSON with this shape:

```json
[
  {
    "candidate_id": "api_candidate_...",
    "decision": "ready_for_row|needs_more_evidence|native_only|reject",
    "replication_kind": "direct_replication|close_replication|clinical_followup|independent_validation|other",
    "row_policy": "strict_figure1a|d_equivalent_figure1b|native_only|coverage_only|reject",
    "original": {
      "title": "", "authors_year": "", "doi": "", "pmid": "", "pmcid": "",
      "study_or_experiment": "", "outcome": "", "contrast": "",
      "n": "", "effect": "", "effect_metric": "",
      "verbatim_effect_text": "", "verbatim_n_text": "",
      "source_url": "", "locator": ""
    },
    "replication": {
      "title": "", "authors_year": "", "doi": "", "pmid": "", "pmcid": "",
      "study_or_experiment": "", "outcome": "", "contrast": "",
      "n": "", "effect": "", "effect_metric": "",
      "verbatim_effect_text": "", "verbatim_n_text": "",
      "source_url": "", "locator": ""
    },
    "relationship_evidence": {
      "verbatim_text": "", "source_url": "", "locator": ""
    },
    "conversion": {
      "route": "native_d|means_sds_to_d|t_to_d|f_to_d|r_to_d|event_counts_to_logor_to_d|native_only|none",
      "formula": "", "computed_original_d": null, "computed_replication_d": null,
      "assumptions": []
    },
    "source_objects_to_mirror": [],
    "blockers": [],
    "notes": ""
  }
]
```

Machine-readable queue: `steps/individual_replication_papers/figure1/auto_mining/individual-paper-gpt-handoff-after-auto-mining.tsv`

## Priority Candidates

### Priority 1 - api_candidate_006071e798115bf1

- Candidate: Shenhav/Rand/Greene intuitive mindset and belief in God
- Route/decision: `coverage_only` / `not_row_original_effect_not_sufficiently_exposed`
- Original:  ()
- Replication:  ()
- Source URLs: none recorded
- Local files already mirrored: data/raw/replication_projects/individual_search_batch006/api_candidate_006071e798115bf1/01_academicrepository_khas_edu_tr_handle_20_500_12469_2831_d0bd654fa705.html [html_or_xml, 1254 bytes] | data/raw/replication_projects/individual_search_batch006/api_candidate_006071e798115bf1/02_www_cambridge_org_core_journals_judgment_and_decision_making_article_doe_a1ce03884c97.html [html_or_xml, 1124143 bytes] | data/raw/replication_projects/individual_search_batch006/api_candidate_006071e798115bf1/03_jbaron_org_journal_18_18412_jdm18412_html_76b3d2c676b7.html [html_or_xml, 78246 bytes] | data/raw/replication_projects/individual_search_batch006/api_candidate_006071e798115bf1/04_doaj_org_article_5937e200778e46fa85dc65470859823c_568d6dfc514e.html [html_or_xml, 65105 bytes] | data/raw/replication_projects/individual_search_batch006/api_candidate_006071e798115bf1/05_doaj_org_article_82a252b91a674344b6a5f8d0792f7774_5de1e476642e.html [html_or_xml, 63804 bytes] | data/raw/replication_projects/individual_search_batch006/api_candidate_006071e798115bf1/06_api_osf_io_v2_registrations_734eu_f7ebd2ff263e.html [html_or_xml, 58714 bytes] | data/raw/replication_projects/individual_search_batch006/api_candidate_006071e798115bf1/07_osf_io_dh5e8_c1df7be23f68.html [html, 4190 bytes] | data/raw/replication_projects/individual_search_batch006/api_candidate_006071e798115bf1/08_openalex_org_w2888851667_16b660aaccf6.html [html, 2653 bytes] | data/raw/replication_projects/individual_search_batch006/api_candidate_006071e798115bf1/09_www_cambridge_org_core_journals_judgment_and_decision_making_article_doe_0c3a74662f6a.html [html_or_xml, 1124144 bytes]
- Known original support: Mirrored article says Shenhav et al. (2012; Study 3) randomly assigned 373 MTurk workers to four conditions and the current study omitted two conditions.
- Known replication support: Mirrored article reports a registered replication in Turkey and the main belief-in-God outcome means/SDs and t statistic.
- Conversion/policy note: Open article was mirrored and the registered-replication relation is real. The article reports original Study 3 N = 373 across four conditions and replication results for two conditions, but it uses assumed/reanalyzed small d values for planning rather than the matched original reported effect for the exact plotted contrast.
- Task: Extract Shenhav/Rand/Greene original two-condition effect and N for the intuitive-mindset belief-in-God target, then map to the replication t/N.

### Priority 1 - api_candidate_0eb40892da116803

- Candidate: the benefit of approximate arithmetic training for symbolic arithmetic fluency in adults -> Failure to replicate the benefit of approximate arithmetic training for symbolic arithmetic fluency in adults
- Route/decision: `coverage_only` / `source_blocked_needs_value_bearing_article`
- Original: the benefit of approximate arithmetic training for symbolic arithmetic fluency in adults ()
- Replication: Failure to replicate the benefit of approximate arithmetic training for symbolic arithmetic fluency in adults (10.1016/j.cognition.2020.104521)
- Source URLs: https://doi.org/10.1016/j.cognition.2020.104521
- Local files already mirrored: data/raw/replication_projects/individual_search_batch006/api_candidate_0eb40892da116803/01_linkinghub_elsevier_com_retrieve_pii_s0010027720303401_8df7563a6ca2.html [html, 2724 bytes] | data/raw/replication_projects/individual_auto_mining_blockers/api_candidate_0eb40892da116803/doi_resolver__10_1016_j_cognition_2020_104521__linkinghub_elsevier_com__8df7563a6ca2.html [html, 2724 bytes] | data/raw/replication_projects/individual_auto_mining_blockers/api_candidate_0eb40892da116803/embedded_pdf__6335b4e39f66__nihms-1651217.pdf [html_or_xml, 1816 bytes] | data/raw/replication_projects/individual_auto_mining_blockers/api_candidate_0eb40892da116803/openalex_landing_page_url__10_1016_j_cognition_2020_104521__pmc_ncbi_nlm_nih_gov__64d337b87b00.html [html_or_xml, 215332 bytes] | data/raw/replication_projects/individual_auto_mining_blockers/api_candidate_0eb40892da116803/openalex_landing_page_url__10_1016_j_cognition_2020_104521__pmc_ncbi_nlm_nih_gov__681bacb13b61.html [html_or_xml, 215332 bytes] | data/raw/replication_projects/individual_auto_mining_blockers/api_candidate_0eb40892da116803/openalex_landing_page_url__10_1016_j_cognition_2020_104521__pubmed_ncbi_nlm_nih_gov__64fca7c3b6fc.html [html_or_xml, 147679 bytes] | data/raw/replication_projects/individual_auto_mining_blockers/api_candidate_0eb40892da116803/openalex_landing_page_url__10_1016_j_cognition_2020_104521__pubmed_ncbi_nlm_nih_gov__98c4d7ea6ea6.html [html_or_xml, 147679 bytes]
- Known original support: none
- Known replication support: none
- Conversion/policy note: Do not promote from metadata alone. The batch found affirmative replication-language evidence, but did not mirror enough value-bearing source text for a matched original effect, original N, replication effect, and replication N under the current Figure 1 row policy.
- Task: Acquire the Cognition approximate-arithmetic replication and original Park/Brannon target source; extract matched symbolic arithmetic fluency effect/N.

### Priority 1 - api_candidate_64a39a53876c51c1

- Candidate: unresolved original target -> Four (and a Half) Preregistered Failures to Replicate the Weapon Focus Effect in Online Samples.
- Route/decision: `coverage_only` / `source_blocked_original_n_or_target_effect_missing`
- Original: Pickel and Sneyd (2018; Experiment 2) ()
- Replication: Four (and a Half) Preregistered Failures to Replicate the Weapon Focus Effect in Online Samples. (10.1037/law0000469)
- Source URLs: https://doi.org/10.1037/law0000469 | https://pmc.ncbi.nlm.nih.gov/articles/PMC12610937/ | https://pubmed.ncbi.nlm.nih.gov/41234291/
- Local files already mirrored: data/raw/replication_projects/individual_search_batch006/api_candidate_64a39a53876c51c1/01_psycnet_apa_org_443_doilanding_doi_10_1037_law0000469_64104e8822dc.html [html_or_xml, 7946 bytes] | data/raw/replication_projects/individual_search_batch006/api_candidate_64a39a53876c51c1/02_pmc_ncbi_nlm_nih_gov_articles_pmc12610937_d5386ee1d706.html [html_or_xml, 284398 bytes] | data/raw/replication_projects/individual_search_batch006/api_candidate_64a39a53876c51c1/03_pubmed_ncbi_nlm_nih_gov_41234291_9c3b5f3a6df6.html [html_or_xml, 124251 bytes] | data/raw/replication_projects/individual_auto_mining_blockers/api_candidate_64a39a53876c51c1/openalex_landing_page_url__10_1037_law0000469__pubmed_ncbi_nlm_nih_gov__6685cfd787f7.html [html_or_xml, 124251 bytes] | data/raw/replication_projects/individual_auto_mining_blockers/api_candidate_64a39a53876c51c1/openalex_landing_page_url__10_1037_law0000469__pubmed_ncbi_nlm_nih_gov__a4d4de9df92d.html [html_or_xml, 124251 bytes] | data/raw/replication_projects/individual_auto_mining_blockers/api_candidate_64a39a53876c51c1/semantic_scholar_landing_page__10_1037_law0000469__www_semanticscholar_org__43f2b75ad98e.html [html_or_xml, 2461 bytes]
- Known original support: Mirrored PMC article says the power analysis used Pickel and Sneyd (2018; Experiment 2; White/Neutral condition) target-description d approximately 2.03.
- Known replication support: Mirrored PMC article reports five preregistered experiments and random-effects meta-analysis of target-description accuracy g = -0.138.
- Conversion/policy note: Open PMC article was mirrored and reports five preregistered experiments with total n = 1,316 plus a meta-analytic target-description g = -0.138. It also reports a source-planning original target-description d approximately 2.03 from Pickel and Sneyd (2018, Experiment 2), but this batch did not resolve the original paper's actual analyzed N and exact outcome row.
- Task: Resolve Pickel and Sneyd (2018) Experiment 2 original N/effect and map it to the replication's target-description or lineup outcome.

### Priority 1 - api_candidate_710fd7eb55fc9d77

- Candidate: Scopolamine's Antidepressant Efficacy in Major Depressive Disorder -> Replication of Scopolamine's Antidepressant Efficacy in Major Depressive Disorder: A Randomized, Placebo-Controlled Clinical Trial
- Route/decision: `coverage_only` / `source_blocked_original_article_value_missing`
- Original: Scopolamine's Antidepressant Efficacy in Major Depressive Disorder ()
- Replication: Replication of Scopolamine's Antidepressant Efficacy in Major Depressive Disorder: A Randomized, Placebo-Controlled Clinical Trial (10.1016/j.biopsych.2009.11.021)
- Source URLs: https://doi.org/10.1016/j.biopsych.2009.11.021
- Local files already mirrored: data/raw/replication_projects/individual_search_batch002/api_candidate_710fd7eb55fc9d77/01_linkinghub_elsevier_com_retrieve_pii_s0006322309014140_e1444cde4e85.html [html, 2741 bytes] | data/raw/replication_projects/individual_search_batch002/api_candidate_710fd7eb55fc9d77/manual/jama_original_html.html [html_or_xml, 5511 bytes] | data/raw/replication_projects/individual_search_batch002/api_candidate_710fd7eb55fc9d77/manual/original_attempts/01.pdf [html_or_xml, 5674 bytes] | data/raw/replication_projects/individual_search_batch002/api_candidate_710fd7eb55fc9d77/manual/original_attempts/02.html [html_or_xml, 5737 bytes] | data/raw/replication_projects/individual_search_batch002/api_candidate_710fd7eb55fc9d77/manual/original_attempts/03.html [html_or_xml, 5680 bytes] | data/raw/replication_projects/individual_search_batch002/api_candidate_710fd7eb55fc9d77/manual/original_attempts/04.html [html_or_xml, 5632 bytes] | data/raw/replication_projects/individual_search_batch002/api_candidate_710fd7eb55fc9d77/manual/original_attempts/05.html [html_or_xml, 5665 bytes] | data/raw/replication_projects/individual_search_batch002/api_candidate_710fd7eb55fc9d77/manual/pmc_scopolamine_html.html [html_or_xml, 179426 bytes] | data/raw/replication_projects/individual_search_batch002/api_candidate_710fd7eb55fc9d77/manual/wisc_scopolamine_pdf.pdf [pdf, 539089 bytes] | data/raw/replication_projects/individual_search_batch002/api_candidate_710fd7eb55fc9d77/manual/wisc_scopolamine_pdf.txt [txt, 41499 bytes] | data/raw/replication_projects/individual_auto_mining_blockers/api_candidate_710fd7eb55fc9d77/doi_resolver__10_1016_j_biopsych_2009_11_021__linkinghub_elsevier_com__e1444cde4e85.html [html, 2741 bytes] | data/raw/replication_projects/individual_auto_mining_blockers/api_candidate_710fd7eb55fc9d77/embedded_pdf__0757fa465543__nihms170258.pdf [html_or_xml, 1817 bytes] | data/raw/replication_projects/individual_auto_mining_blockers/api_candidate_710fd7eb55fc9d77/openalex_landing_page_url__10_1016_j_biopsych_2009_11_021__pmc_ncbi_nlm_nih_gov__510404a069c2.html [html_or_xml, 179426 bytes] | data/raw/replication_projects/individual_auto_mining_blockers/api_candidate_710fd7eb55fc9d77/openalex_landing_page_url__10_1016_j_biopsych_2009_11_021__pubmed_ncbi_nlm_nih_gov__2860fa381db8.html [html_or_xml, 162461 bytes] | ... 2 more local files omitted from prompt row
- Known original support: Mirrored replication PMC/PDF reports the initial scopolamine trial as total n = 18 with MDD n = 9 and bipolar disorder n = 9; direct JAMA original article acquisition attempts were blocked by the publisher/CAPTCHA route.
- Known replication support: Mirrored replication PMC/PDF reports n = 23 randomized, 22 analyzed, and source-reported scopolamine-placebo effect sizes d = 1.2 and d = 1.7 for Blocks 1 and 2.
- Conversion/policy note: Do not promote until the original value-bearing article or an authoritative mirrored source provides the selected original effect size and exact outcome locator.
- Task: Acquire the original scopolamine antidepressant article or authoritative table and determine the matched crossover D/N route for the replication.

### Priority 1 - api_candidate_821f217890822e88

- Candidate: the Mehta and Zhu (2009) color-priming effect on anagram solution times -> Failure to replicate the Mehta and Zhu (2009) color-priming effect on anagram solution times
- Route/decision: `coverage_only` / `source_blocked_needs_value_bearing_article`
- Original: the Mehta and Zhu (2009) color-priming effect on anagram solution times ()
- Replication: Failure to replicate the Mehta and Zhu (2009) color-priming effect on anagram solution times (10.3758/s13423-013-0548-3)
- Source URLs: https://doi.org/10.3758/s13423-013-0548-3
- Local files already mirrored: data/raw/replication_projects/individual_search_batch006/api_candidate_821f217890822e88/01_link_springer_com_article_10_3758_s13423_013_0548_3_error_cookies_not_su_6018d0080996.html [html_or_xml, 300091 bytes] | data/raw/replication_projects/individual_auto_mining_blockers/api_candidate_821f217890822e88/doi_resolver__10_3758_s13423_013_0548_3__link_springer_com__4c9d8d11264e.html [html_or_xml, 294622 bytes] | data/raw/replication_projects/individual_auto_mining_blockers/api_candidate_821f217890822e88/doi_resolver__10_3758_s13423_013_0548_3__link_springer_com__eb3e95f0a2bc.html [html_or_xml, 294622 bytes] | data/raw/replication_projects/individual_auto_mining_blockers/api_candidate_821f217890822e88/embedded_pdf__41aec7058c75__s13423-013-0548-3.pdf [pdf, 186357 bytes] | data/raw/replication_projects/individual_auto_mining_blockers/api_candidate_821f217890822e88/openalex_landing_page_url__10_3758_s13423_013_0548_3__pubmed_ncbi_nlm_nih_gov__58712b75692d.html [html_or_xml, 120686 bytes] | data/raw/replication_projects/individual_auto_mining_blockers/api_candidate_821f217890822e88/openalex_landing_page_url__10_3758_s13423_013_0548_3__pubmed_ncbi_nlm_nih_gov__7dd9d03be342.html [html_or_xml, 120686 bytes]
- Known original support: none
- Known replication support: none
- Conversion/policy note: Do not promote from metadata alone. The batch found affirmative replication-language evidence, but did not mirror enough value-bearing source text for a matched original effect, original N, replication effect, and replication N under the current Figure 1 row policy.
- Task: Decide whether the Mehta/Zhu anagram color-priming interaction can be converted to a defensible Figure 1 D row; if yes, return exact original and replication effect/N with formula.

### Priority 1 - api_candidate_a939357d526cdfa3

- Candidate: Griskevicius et al. (2010) -> Collaborative Registered Replication of Griskevicius et al. (2010): Can Pro-environmental Behavior Be Promoted by Priming Status Motivation?
- Route/decision: `coverage_only` / `source_blocked_needs_value_bearing_article`
- Original: Griskevicius et al. (2010) ()
- Replication: Collaborative Registered Replication of Griskevicius et al. (2010): Can Pro-environmental Behavior Be Promoted by Priming Status Motivation? (10.1525/collabra.143773)
- Source URLs: https://online.ucpress.edu/collabra/article-pdf/11/1/143773/896724/collabra_2025_11_1_143773.pdf | https://doi.org/10.1525/collabra.143773 | https://reff.f.bg.ac.rs/handle/123456789/7552 | https://research-information.bris.ac.uk/en/publications/d50dbb04-b9d4-47d1-aa5f-31efe8e502a9 | https://hdl.handle.net/1983/d50dbb04-b9d4-47d1-aa5f-31efe8e502a9 | https://openalex.org/W4414275560
- Local files already mirrored: data/raw/replication_projects/individual_search_batch006/api_candidate_a939357d526cdfa3/03_reff_f_bg_ac_rs_handle_123456789_7552_3b77e040e60e.html [html_or_xml, 13278 bytes] | data/raw/replication_projects/individual_search_batch006/api_candidate_a939357d526cdfa3/04_research_information_bris_ac_uk_en_publications_collaborative_registered_73c313ff9c53.html [html_or_xml, 58431 bytes] | data/raw/replication_projects/individual_search_batch006/api_candidate_a939357d526cdfa3/05_research_information_bris_ac_uk_en_publications_collaborative_registered_46d17ff0bf84.html [html_or_xml, 58431 bytes] | data/raw/replication_projects/individual_search_batch006/api_candidate_a939357d526cdfa3/06_openalex_org_w4414275560_16b660aaccf6.html [html, 2653 bytes] | data/raw/replication_projects/individual_auto_mining_blockers/api_candidate_a939357d526cdfa3/openalex_landing_page_url__10_1525_collabra_143773__research_information_bris_ac_uk__064ebea56d86.html [html_or_xml, 58431 bytes] | data/raw/replication_projects/individual_auto_mining_blockers/api_candidate_a939357d526cdfa3/openalex_landing_page_url__10_1525_collabra_143773__research_information_bris_ac_uk__3d4440ba77ba.html [html_or_xml, 58431 bytes] | data/raw/replication_projects/individual_auto_mining_blockers/api_candidate_a939357d526cdfa3/openalex_landing_page_url__10_1525_collabra_143773__research_information_bris_ac_uk__8041eb4c05fa.html [html_or_xml, 58431 bytes] | data/raw/replication_projects/individual_auto_mining_blockers/api_candidate_a939357d526cdfa3/openalex_landing_page_url__10_1525_collabra_143773__research_information_bris_ac_uk__a24bf15f0112.html [html_or_xml, 58431 bytes]
- Known original support: none
- Known replication support: none
- Conversion/policy note: Institutional/repository landing pages were mirrored, but not enough article text or tables for original and replication D/N extraction.
- Task: Find article/supplement/data for the Collabra Griskevicius status-motivation replication and determine the primary pro-environmental-choice D/N row, not only the manipulation-check abstract values.

### Priority 1 - api_candidate_c49eb133d5977b06

- Candidate: Rabbitt (1968) Experiment 2 -> Recall of Speech is Impaired by Subsequent Masking Noise: A Replication of Rabbitt (1968) Experiment 2
- Route/decision: `strict_figure1a` / `manual_acquisition_needed_original_n`
- Original: Rabbitt (1968) Experiment 2 ()
- Replication: Recall of Speech is Impaired by Subsequent Masking Noise: A Replication of Rabbitt (1968) Experiment 2 (10.1080/25742442.2021.1896908)
- Source URLs: https://doi.org/10.1080/25742442.2021.1896908 | https://www.ncbi.nlm.nih.gov/pmc/articles/8262135 | https://openalex.org/W3122990348
- Local files already mirrored: data/raw/replication_projects/individual_search_batch001/api_candidate_c49eb133d5977b06/02_pmc_ncbi_nlm_nih_gov_articles_pmc8262135_f0add6db277d.html [html_or_xml, 143802 bytes] | data/raw/replication_projects/individual_search_batch001/api_candidate_c49eb133d5977b06/03_openalex_org_w3122990348_158469730ed2.html [html, 2653 bytes] | data/raw/replication_projects/individual_search_batch001/api_candidate_c49eb133d5977b06/02_pmc_ncbi_nlm_nih_gov_articles_pmc8262135_5425c883081d.html [html_or_xml, 143802 bytes] | data/raw/replication_projects/individual_search_batch001/api_candidate_c49eb133d5977b06/02_pmc_ncbi_nlm_nih_gov_articles_pmc8262135_6dcd4fd4d23b.html [html_or_xml, 143802 bytes] | data/raw/replication_projects/individual_search_batch002/api_candidate_c49eb133d5977b06/manual/brown_rabbitt_pdf.pdf [pdf, 735910 bytes] | data/raw/replication_projects/individual_search_batch002/api_candidate_c49eb133d5977b06/manual/brown_rabbitt_pdf.txt [txt, 30953 bytes] | data/raw/replication_projects/individual_search_batch002/api_candidate_c49eb133d5977b06/manual/original_attempts/cinii.html [html_or_xml, 89095 bytes] | data/raw/replication_projects/individual_search_batch002/api_candidate_c49eb133d5977b06/manual/original_attempts/doi.html [html_or_xml, 5498 bytes] | data/raw/replication_projects/individual_search_batch002/api_candidate_c49eb133d5977b06/manual/original_attempts/pubmed.html [html_or_xml, 112262 bytes] | data/raw/replication_projects/individual_search_batch002/api_candidate_c49eb133d5977b06/manual/original_attempts/sage_full.html [html_or_xml, 5498 bytes] | data/raw/replication_projects/individual_search_batch002/api_candidate_c49eb133d5977b06/manual/original_attempts/sage_pdf.pdf [html_or_xml, 5531 bytes] | data/raw/replication_projects/individual_search_batch002/api_candidate_c49eb133d5977b06/manual/rabbitt_replication_pmc.html [html_or_xml, 143802 bytes] | data/raw/replication_projects/individual_auto_mining_blockers/api_candidate_c49eb133d5977b06/embedded_pdf__1c22cd936e7e__nihms-1679219.pdf [html_or_xml, 1817 bytes] | data/raw/replication_projects/individual_auto_mining_blockers/api_candidate_c49eb133d5977b06/openalex_landing_page_url__10_1080_25742442_2021_1896908__dialnet_unirioja_es__12b96061995d.html [html_or_xml, 36633 bytes] | ... 2 more local files omitted from prompt row
- Known original support: Mirrored PMC replication reports the original effect as d = 0.19, but does not give the original total N for the focal result.
- Known replication support: Mirrored PMC replication reports a final analyzed replication sample of 200 and d = 0.19.
- Conversion/policy note: Do not promote until original Rabbitt N is extracted from the original article or another value-bearing source.
- Task: Resolve Rabbitt (1968) Experiment 2 original analyzed N and confirm the exact target-description outcome that maps to the open preregistered weapon-focus replication.

### Priority 2 - IND-015

- Candidate: Red-romance preregistered replications
- Route/decision: `strict_figure1a` / `source_blocked_needs_manual_acquisition`
- Original:  ()
- Replication:  ()
- Source URLs: none recorded
- Local files already mirrored: none
- Known original support: Candidate maps to red-romance original targets, but exact original study/outcome rows were not resolved from local bytes.
- Known replication support: Publisher acquisition for the preregistered replication article was blocked or metadata-only in this batch.
- Conversion/policy note: Do not promote until exact original target and replication values are extracted.
- Task: manual_acquisition_of_hogrefe_article_or_author_manuscript

### Priority 2 - IND-017

- Candidate: Signing-at-the-beginning dishonesty direct replication
- Route/decision: `d_equivalent_figure1b` / `source_blocked_needs_manual_acquisition`
- Original:  ()
- Replication:  ()
- Source URLs: none recorded
- Local files already mirrored: none
- Known original support: Candidate relation is strong, but PNAS source bytes with exact values were not mirrored in this batch.
- Known replication support: The high-powered direct replication appears potentially row-eligible, pending source values.
- Conversion/policy note: Could be Figure 1B or strict SMD depending on whether the final endpoint is binary cheating or continuous dishonesty amount.
- Task: manual_acquisition_of_pnas_article_supplement_or_data_code_for_values

### Priority 2 - IND-019

- Candidate: Mating-motive consumer/risk replication studies
- Route/decision: `coverage_worklist` / `source_blocked_needs_manual_acquisition`
- Original:  ()
- Replication:  ()
- Source URLs: none recorded
- Local files already mirrored: data/raw/replication_projects/individual_search_batch001/IND-019/01_psycnet_apa_org_443_doilanding_doi_10_1037_xge0000116_95f52a94846c.html [html_or_xml, 7813 bytes] | data/raw/replication_projects/individual_search_batch001/IND-019/01_psycnet_apa_org_443_doilanding_doi_10_1037_xge0000116_627a68d5258e.html [html_or_xml, 7946 bytes]
- Known original support: Candidate likely contains multiple target mappings, but local source bytes do not expose the supplement/value table.
- Known replication support: Replication values need extraction from the article/supplement.
- Conversion/policy note: Do not collapse multiple original targets without study/outcome-level mapping.
- Task: manual_acquisition_of_jep_general_article_and_supplement

### Priority 2 - IND-022

- Candidate: Early goal-directed therapy mortality follow-up trials
- Route/decision: `d_equivalent_figure1b` / `needs_event_counts_or_open_trial_source_objects`
- Original:  ()
- Replication:  ()
- Source URLs: none recorded
- Local files already mirrored: data/raw/replication_projects/individual_search_batch001/IND-022/05_figshare_com_articles_dataset_promise_trial_data_1359853_444b3c0512cd.html [html_or_xml, 2009 bytes] | data/raw/replication_projects/individual_search_batch001/IND-022/05_figshare_com_articles_dataset_promise_trial_data_1359853_1df22b9dc761.html [html_or_xml, 2009 bytes] | data/raw/replication_projects/individual_search_batch001/IND-022/05_figshare_com_articles_dataset_promise_trial_data_1359853_6cac6983810a.html [html_or_xml, 2009 bytes] | data/raw/replication_projects/individual_search_batch001/IND-022/05_figshare_com_articles_dataset_promise_trial_data_1359853_cad4dc2967c8.html [html_or_xml, 2009 bytes]
- Known original support: Search intake identifies Rivers et al. 2001 as the original EGDT mortality trial, but NEJM source objects were not mirrored in this batch.
- Known replication support: Search intake identifies ProCESS, ARISE, and ProMISe as larger multicenter follow-ups; event counts still need local source extraction.
- Conversion/policy note: Route to D-equivalent Figure 1B only after event counts or OR/RR/RD and baseline risk are extracted.
- Task: mirror_open_trial_reports_or_registry_records_and_extract_event_counts

### Priority 2 - IND-023

- Candidate: Activated protein C severe-sepsis mortality follow-up
- Route/decision: `d_equivalent_figure1b` / `needs_event_counts_or_open_trial_source_objects`
- Original:  ()
- Replication:  ()
- Source URLs: none recorded
- Local files already mirrored: none
- Known original support: Search intake identifies the original PROWESS activated-protein-C severe-sepsis trial, but value-bearing source bytes were not mirrored in this batch.
- Known replication support: Search intake identifies PROWESS-SHOCK as the larger follow-up, but event counts still need local source extraction.
- Conversion/policy note: Route to D-equivalent Figure 1B only after event counts or OR/RR/RD and baseline risk are extracted.
- Task: resolve_nejm_or_open_source_routes_and_extract_mortality_counts

### Priority 2 - IND-024

- Candidate: Intensive insulin/tight glucose control ICU mortality follow-up
- Route/decision: `d_equivalent_figure1b` / `needs_event_counts_or_open_trial_source_objects`
- Original:  ()
- Replication:  ()
- Source URLs: none recorded
- Local files already mirrored: none
- Known original support: Search intake identifies van den Berghe et al. 2001 as the original intensive-insulin ICU trial, but value-bearing source bytes were not mirrored in this batch.
- Known replication support: Search intake identifies NICE-SUGAR as the larger follow-up with N = 6104, but event counts still need local extraction.
- Conversion/policy note: Route to D-equivalent Figure 1B only after event counts or OR/RR/RD and baseline risk are extracted.
- Task: resolve_nejm_or_open_source_routes_and_extract_mortality_counts

### Priority 2 - api_candidate_025c30471725eba5

- Candidate: Auditory religious cues and dishonest behavior
- Route/decision: `coverage_only` / `not_row_conceptual_extension_no_single_original_effect`
- Original:  ()
- Replication:  ()
- Source URLs: none recorded
- Local files already mirrored: data/raw/replication_projects/individual_search_batch004/api_candidate_025c30471725eba5/01_journals_plos_org_plosone_article_id_10_1371_journal_pone_0237007_f5db93457e71.html [html_or_xml, 281893 bytes]
- Known original support: Mirrored PLOS article frames the work as replicating and extending religious priming effects but cites several prior religious-prime/prosociality sources rather than resolving a single original D/N target.
- Known replication support: The article reports N = 408 and moderation by religiosity/ritual participation in a dishonest-behavior game.
- Conversion/policy note: Do not promote without a single original paper, matched outcome, and original effect/N. Keep as context for religious-priming replication mining.
- Task: retain_as_context_source_until_exact_original_target_is_resolved

### Priority 2 - api_candidate_0367fa32a3d09f7b

- Candidate: Loftus (1979) -> Does blatantly contradictory information reduce the misinformation effect? A Registered Report replication of Loftus (1979)
- Route/decision: `coverage_only` / `source_blocked_needs_value_bearing_article`
- Original: Loftus (1979) ()
- Replication: Does blatantly contradictory information reduce the misinformation effect? A Registered Report replication of Loftus (1979) (10.1111/lcrp.12242)
- Source URLs: https://doi.org/10.1111/lcrp.12242
- Local files already mirrored: none
- Known original support: none
- Known replication support: none
- Conversion/policy note: Do not promote from metadata alone. The batch found affirmative replication-language evidence, but did not mirror enough value-bearing source text for a matched original effect, original N, replication effect, and replication N under the current Figure 1 row policy.
- Task: Acquire the Loftus misinformation registered-report replication and extract matched original/replication effect/N if publicly available.

### Priority 2 - api_candidate_112b3ad59e12752d

- Candidate: Prosocial spending and post-windfall happiness original specification
- Route/decision: `strict_figure1a` / `not_row_original_effect_not_sufficiently_exposed`
- Original:  ()
- Replication:  ()
- Source URLs: none recorded
- Local files already mirrored: data/raw/replication_projects/individual_search_batch003/api_candidate_112b3ad59e12752d/01_journals_plos_org_plosone_article_id_10_1371_journal_pone_0272434_be76b034e1b0.html [html_or_xml, 163309 bytes]
- Known original support: Mirrored PLOS article reports the Dunn et al. original experiment N = 46 and original p = .042 for the focal analysis, but does not expose a matched original D or enough original ANCOVA inputs.
- Known replication support: Mirrored PLOS article reports replication N = 133 and original-specification result F(1,130) = .35, p = .557, partial eta squared = .001.
- Conversion/policy note: Do not promote until the original article or supplement supplies a matched effect size/statistic sufficient for the same ANCOVA-style endpoint.
- Task: manual_acquisition_of_original_dunn_aknin_norton_value_inputs_if_prioritized

### Priority 2 - api_candidate_44137bf63c3bbdfa

- Candidate: Schiller et al. (Nature, 2010) -> Registered Replication of Schiller et al. (Nature, 2010)
- Route/decision: `coverage_only` / `source_blocked_protocol_or_repository_only`
- Original: Schiller et al. (Nature, 2010) ()
- Replication: Registered Replication of Schiller et al. (Nature, 2010) (10.17605/osf.io/k2w4a)
- Source URLs: https://doi.org/10.17605/osf.io/k2w4a | https://osf.io/k2w4a/ | 10.17605/osf.io/k2w4a
- Local files already mirrored: data/raw/replication_projects/individual_search_batch006/api_candidate_44137bf63c3bbdfa/01_osf_io_k2w4a_c1df7be23f68.html [html, 4190 bytes] | data/raw/replication_projects/individual_search_batch006/api_candidate_44137bf63c3bbdfa/02_osf_io_k2w4a_c1df7be23f68.html [html, 4190 bytes] | data/raw/replication_projects/individual_search_batch006/api_candidate_44137bf63c3bbdfa/03_osf_io_k2w4a_c1df7be23f68.html [html, 4190 bytes] | data/raw/replication_projects/individual_auto_mining_blockers/api_candidate_44137bf63c3bbdfa/doi_resolver__10_17605_osf_io_k2w4a__osf_io__c1df7be23f68.html [html, 4190 bytes]
- Known original support: Triage resolved the target as Schiller et al. (Nature, 2010), but only the OSF registration DOI was routed.
- Known replication support: The mirrored/source URLs identify a Registered Replication of Schiller et al. record, not extracted result values.
- Conversion/policy note: The candidate is an OSF registration/source package rather than a value-bearing replication article in this batch. It should remain a no-repull target until a completed paper/result source is resolved.
- Task: resolve_completed_replication_article_or_results_package_before_value_extraction

### Priority 2 - api_candidate_49040530056b1fbf

- Candidate: van Prooijen (2017) -> Education and conspiracy beliefs: A replication of van Prooijen (2017)
- Route/decision: `coverage_only` / `source_blocked_needs_value_bearing_article`
- Original: van Prooijen (2017) ()
- Replication: Education and conspiracy beliefs: A replication of van Prooijen (2017) (10.1002/acp.4037)
- Source URLs: https://doi.org/10.1002/acp.4037
- Local files already mirrored: data/raw/replication_projects/individual_auto_mining_blockers/api_candidate_49040530056b1fbf/semantic_scholar_landing_page__10_1002_acp_4037__www_semanticscholar_org__8ce2c9e363df.html [html_or_xml, 2461 bytes]
- Known original support: none
- Known replication support: none
- Conversion/policy note: Do not promote from metadata alone. The batch found affirmative replication-language evidence, but did not mirror enough value-bearing source text for a matched original effect, original N, replication effect, and replication N under the current Figure 1 row policy.
- Task: manual_acquisition_or_repository_parse_if_prioritized

### Priority 2 - api_candidate_4dc2cff8320f0b0e

- Candidate: Reactions to female- versus male-favoring sex differences
- Route/decision: `coverage_only` / `not_row_original_effect_and_d_route_not_sufficiently_exposed`
- Original:  ()
- Replication:  ()
- Source URLs: none recorded
- Local files already mirrored: data/raw/replication_projects/individual_search_batch006/api_candidate_4dc2cff8320f0b0e/01_journals_plos_org_plosone_article_id_10_1371_journal_pone_0266171_7c8e7ffc22d0.html [html_or_xml, 161894 bytes] | data/raw/replication_projects/individual_search_batch006/api_candidate_4dc2cff8320f0b0e/02_pmc_ncbi_nlm_nih_gov_articles_pmc8967052_13d49c6d103e.html [html_or_xml, 157247 bytes] | data/raw/replication_projects/individual_search_batch006/api_candidate_4dc2cff8320f0b0e/03_pubmed_ncbi_nlm_nih_gov_35353872_31bee0960424.html [html_or_xml, 132712 bytes]
- Known original support: Mirrored PLOS article says the study is a direct replication of the authors' earlier study on reactions to sex-difference findings.
- Known replication support: Mirrored abstract reports 303 participants and replicated the less-positive reaction to male-favoring differences.
- Conversion/policy note: Open PLOS/PMC article was mirrored and the direct-replication relation is real. The article reports a multi-factor reaction-score replication with the earlier study as context, but this batch did not extract a matched original D/N and replication D/N for a single focal outcome.
- Task: retain_as_context_until_original_effect_and_single_outcome_d_route_are_extracted

### Priority 2 - api_candidate_53e20f8627a320c7

- Candidate: past findings regarding positive affirmations and self-esteem -> On the failure to replicate past findings regarding positive affirmations and self-esteem
- Route/decision: `coverage_only` / `source_blocked_needs_value_bearing_article`
- Original: past findings regarding positive affirmations and self-esteem ()
- Replication: On the failure to replicate past findings regarding positive affirmations and self-esteem (10.1016/j.jcbs.2020.03.003)
- Source URLs: https://doi.org/10.1016/j.jcbs.2020.03.003
- Local files already mirrored: data/raw/replication_projects/individual_search_batch006/api_candidate_53e20f8627a320c7/01_linkinghub_elsevier_com_retrieve_pii_s2212144719301103_bd49689bf85e.html [html, 2704 bytes] | data/raw/replication_projects/individual_auto_mining_blockers/api_candidate_53e20f8627a320c7/doi_resolver__10_1016_j_jcbs_2020_03_003__linkinghub_elsevier_com__bd49689bf85e.html [html, 2704 bytes]
- Known original support: none
- Known replication support: none
- Conversion/policy note: Do not promote from metadata alone. The batch found affirmative replication-language evidence, but did not mirror enough value-bearing source text for a matched original effect, original N, replication effect, and replication N under the current Figure 1 row policy.
- Task: manual_acquisition_or_repository_parse_if_prioritized

### Priority 2 - api_candidate_5d432a85cc83bb79

- Candidate: the effects of self-construal priming on spatial memory recall -> Cognition and the self: Attempt of an independent close replication of the effects of self-construal priming on spatial memory recall
- Route/decision: `coverage_only` / `source_blocked_needs_value_bearing_article`
- Original: the effects of self-construal priming on spatial memory recall ()
- Replication: Cognition and the self: Attempt of an independent close replication of the effects of self-construal priming on spatial memory recall (10.1016/j.jesp.2017.08.005)
- Source URLs: https://doi.org/10.1016/j.jesp.2017.08.005
- Local files already mirrored: data/raw/replication_projects/individual_search_batch006/api_candidate_5d432a85cc83bb79/01_linkinghub_elsevier_com_retrieve_pii_s0022103117302792_a27eb70e6f9a.html [html, 2748 bytes] | data/raw/replication_projects/individual_auto_mining_blockers/api_candidate_5d432a85cc83bb79/doi_resolver__10_1016_j_jesp_2017_08_005__linkinghub_elsevier_com__a27eb70e6f9a.html [html, 2748 bytes] | data/raw/replication_projects/individual_auto_mining_blockers/api_candidate_5d432a85cc83bb79/openalex_landing_page_url__10_1016_j_jesp_2017_08_005__api_osf_io__47b17b104376.bin [json_like, 6512 bytes] | data/raw/replication_projects/individual_auto_mining_blockers/api_candidate_5d432a85cc83bb79/openalex_landing_page_url__10_1016_j_jesp_2017_08_005__osf_io__c1df7be23f68.html [html, 4190 bytes]
- Known original support: none
- Known replication support: none
- Conversion/policy note: Do not promote from metadata alone. The batch found affirmative replication-language evidence, but did not mirror enough value-bearing source text for a matched original effect, original N, replication effect, and replication N under the current Figure 1 row policy.
- Task: manual_acquisition_or_repository_parse_if_prioritized

### Priority 2 - api_candidate_705797b93ca7def0

- Candidate: Schuler and Wänke (2016) -> Does Subjective SES Moderate the Effect of Money Priming on Socioeconomic System Support? A Replication of Schuler and Wänke (2016)
- Route/decision: `coverage_only` / `source_blocked_needs_value_bearing_article`
- Original: Schuler and Wänke (2016) ()
- Replication: Does Subjective SES Moderate the Effect of Money Priming on Socioeconomic System Support? A Replication of Schuler and Wänke (2016) (10.1177/1948550617740941)
- Source URLs: https://doi.org/10.1177/1948550617740941
- Local files already mirrored: data/raw/replication_projects/individual_auto_mining_blockers/api_candidate_705797b93ca7def0/semantic_scholar_landing_page__10_1177_1948550617740941__www_semanticscholar_org__3ed038622535.html [html_or_xml, 2461 bytes]
- Known original support: none
- Known replication support: none
- Conversion/policy note: Do not promote from metadata alone. The batch found affirmative replication-language evidence, but did not mirror enough value-bearing source text for a matched original effect, original N, replication effect, and replication N under the current Figure 1 row policy.
- Task: manual_acquisition_or_repository_parse_if_prioritized

### Priority 2 - api_candidate_74f56abca426fbc9

- Candidate: the Results of Ciani and Sheldon (2010) -> Is Intelligence Enhanced by Letter Priming? A Failure to Replicate the Results of Ciani and Sheldon (2010)
- Route/decision: `coverage_only` / `source_blocked_needs_value_bearing_article`
- Original: the Results of Ciani and Sheldon (2010) ()
- Replication: Is Intelligence Enhanced by Letter Priming? A Failure to Replicate the Results of Ciani and Sheldon (2010) (10.2466/04.03.pr0.112.2.533-544)
- Source URLs: https://doi.org/10.2466/04.03.pr0.112.2.533-544
- Local files already mirrored: data/raw/replication_projects/individual_auto_mining_blockers/api_candidate_74f56abca426fbc9/openalex_landing_page_url__10_2466_04_03_pr0_112_2_533_544__pubmed_ncbi_nlm_nih_gov__c1cfdd48916c.html [html_or_xml, 119067 bytes] | data/raw/replication_projects/individual_auto_mining_blockers/api_candidate_74f56abca426fbc9/openalex_landing_page_url__10_2466_04_03_pr0_112_2_533_544__pubmed_ncbi_nlm_nih_gov__d6b55411ea53.html [html_or_xml, 119067 bytes]
- Known original support: none
- Known replication support: none
- Conversion/policy note: Do not promote from metadata alone. The batch found affirmative replication-language evidence, but did not mirror enough value-bearing source text for a matched original effect, original N, replication effect, and replication N under the current Figure 1 row policy.
- Task: manual_acquisition_or_repository_parse_if_prioritized

### Priority 2 - api_candidate_7c25e95e83db7d9a

- Candidate: Randomized Controlled Trial Results for Carotid Endarterectomy -> Real-World Replication of Randomized Controlled Trial Results for Carotid Endarterectomy
- Route/decision: `native_only` / `source_blocked_clinical_observational_validation_not_current_pair`
- Original: Randomized Controlled Trial Results for Carotid Endarterectomy ()
- Replication: Real-World Replication of Randomized Controlled Trial Results for Carotid Endarterectomy (10.1001/archneur.64.10.1496)
- Source URLs: https://doi.org/10.1001/archneur.64.10.1496
- Local files already mirrored: data/raw/replication_projects/individual_auto_mining_blockers/api_candidate_7c25e95e83db7d9a/openalex_landing_page_url__10_1001_archneur_64_10_1496__ora_ox_ac_uk__852d7e9b6654.html [html_or_xml, 61178 bytes] | data/raw/replication_projects/individual_auto_mining_blockers/api_candidate_7c25e95e83db7d9a/openalex_landing_page_url__10_1001_archneur_64_10_1496__ora_ox_ac_uk__e2e00e094e42.html [html_or_xml, 61178 bytes] | data/raw/replication_projects/individual_auto_mining_blockers/api_candidate_7c25e95e83db7d9a/openalex_landing_page_url__10_1001_archneur_64_10_1496__pubmed_ncbi_nlm_nih_gov__46a0c7f378ef.html [html_or_xml, 145814 bytes] | data/raw/replication_projects/individual_auto_mining_blockers/api_candidate_7c25e95e83db7d9a/openalex_landing_page_url__10_1001_archneur_64_10_1496__pubmed_ncbi_nlm_nih_gov__d8113d58532b.html [html_or_xml, 145814 bytes]
- Known original support: Candidate title indicates a real-world replication/validation of RCT results, but the JAMA route was blocked by 403 and no matched event-count pair was mirrored.
- Known replication support: No value-bearing source object was mirrored locally for this batch.
- Conversion/policy note: Keep as clinical context/manual acquisition; do not treat as Figure 1B without event counts and a specific trial-to-follow-up mapping.
- Task: manual_acquisition_if_clinical_real_world_validation_rows_are_in_scope

### Priority 2 - api_candidate_96a758378eb37b0e

- Candidate: in the rapid naming task -> Phonological priming: Failure to replicate in the rapid naming task
- Route/decision: `coverage_only` / `source_blocked_needs_value_bearing_article`
- Original: in the rapid naming task ()
- Replication: Phonological priming: Failure to replicate in the rapid naming task (10.3758/bf03334046)
- Source URLs: https://doi.org/10.3758/bf03334046
- Local files already mirrored: data/raw/replication_projects/individual_search_batch006/api_candidate_96a758378eb37b0e/01_link_springer_com_article_10_3758_bf03334046_error_cookies_not_supported_298b26a951ab.html [html_or_xml, 244411 bytes] | data/raw/replication_projects/individual_auto_mining_blockers/api_candidate_96a758378eb37b0e/doi_resolver__10_3758_bf03334046__link_springer_com__3b1aab19bff8.html [html_or_xml, 238112 bytes] | data/raw/replication_projects/individual_auto_mining_blockers/api_candidate_96a758378eb37b0e/doi_resolver__10_3758_bf03334046__link_springer_com__acfd9f712379.html [html_or_xml, 244282 bytes] | data/raw/replication_projects/individual_auto_mining_blockers/api_candidate_96a758378eb37b0e/embedded_pdf__4a772153e936__BF03334046.pdf [pdf, 1096288 bytes] | data/raw/replication_projects/individual_auto_mining_blockers/api_candidate_96a758378eb37b0e/openalex_oa_url__10_3758_bf03334046__link_springer_com__ce365607a87b.pdf [pdf, 1096288 bytes] | data/raw/replication_projects/individual_auto_mining_blockers/api_candidate_96a758378eb37b0e/semantic_scholar_landing_page__10_3758_bf03334046__www_semanticscholar_org__cb400cd20894.html [html_or_xml, 2461 bytes]
- Known original support: none
- Known replication support: none
- Conversion/policy note: Do not promote from metadata alone. The batch found affirmative replication-language evidence, but did not mirror enough value-bearing source text for a matched original effect, original N, replication effect, and replication N under the current Figure 1 row policy.
- Task: Determine whether the phonological-priming rapid-naming paper is a valid close/direct row or should be rejected because the task differs from Hillinger's lexical-decision original.

### Priority 2 - api_candidate_9db26ff9b8058473

- Candidate: Social-distance priming Study 1 near-versus-far food-judgment replication
- Route/decision: `strict_figure1a` / `not_row_replication_n_not_larger_or_original_effect_missing`
- Original:  ()
- Replication:  ()
- Source URLs: none recorded
- Local files already mirrored: data/raw/replication_projects/individual_search_batch001/api_candidate_9db26ff9b8058473/01_journals_plos_org_plosone_article_file_id_10_1371_journal_pone_0042510_t_6c57bac0ed58.pdf [pdf, 251094 bytes] | data/raw/replication_projects/individual_search_batch001/api_candidate_9db26ff9b8058473/02_journals_plos_org_plosone_article_id_10_1371_journal_pone_0042510_b6712e218027.html [html_or_xml, 161472 bytes] | data/raw/replication_projects/individual_search_batch001/api_candidate_9db26ff9b8058473/03_pubmed_ncbi_nlm_nih_gov_22952597_586846f50ecf.html [html_or_xml, 158823 bytes] | data/raw/replication_projects/individual_search_batch001/api_candidate_9db26ff9b8058473/05_journals_plos_org_plosone_article_id_10_1371_journal_pone_0042510_b6712e218027.html [html_or_xml, 161472 bytes] | data/raw/replication_projects/individual_search_batch001/api_candidate_9db26ff9b8058473/06_doaj_org_article_e8e46da29cce40e8a55999b5cda66f5d_d1a30f9535c8.html [html_or_xml, 61227 bytes] | data/raw/replication_projects/individual_search_batch001/api_candidate_9db26ff9b8058473/07_pmc_ncbi_nlm_nih_gov_articles_pmc3430642_33c0ec5ac84f.html [html_or_xml, 154934 bytes] | data/raw/replication_projects/individual_search_batch001/api_candidate_9db26ff9b8058473/08_openalex_org_w2106777508_158469730ed2.html [html, 2653 bytes] | data/raw/replication_projects/individual_search_batch001/api_candidate_9db26ff9b8058473/03_pubmed_ncbi_nlm_nih_gov_22952597_0e7131dc0940.html [html_or_xml, 158823 bytes] | data/raw/replication_projects/individual_search_batch001/api_candidate_9db26ff9b8058473/03_pubmed_ncbi_nlm_nih_gov_22952597_47e83895724e.html [html_or_xml, 158823 bytes] | data/raw/replication_projects/individual_search_batch001/api_candidate_9db26ff9b8058473/07_pmc_ncbi_nlm_nih_gov_articles_pmc3430642_d9760d492c6e.html [html_or_xml, 154934 bytes] | data/raw/replication_projects/individual_search_batch001/api_candidate_9db26ff9b8058473/07_pmc_ncbi_nlm_nih_gov_articles_pmc3430642_f0e81aaab47f.html [html_or_xml, 154934 bytes]
- Known original support: Mirrored PLOS paper Table 1 reports Williams and Bargh Study 4 d = 0.76, calculated from t = -2.86 assuming equal 28 participants per group.
- Known replication support: Mirrored PLOS paper reports Study 1 analyzed N = 71 after exclusions, with focal close/far cells 22 and 22; the focal replication N is therefore smaller than the original focal N.
- Conversion/policy note: The clean focal contrast fails the current larger-replication-N rule. The companion Study 2 may be usable only after original Study 3 effect extraction.
- Task: do_not_promote_unless_policy_allows_smaller_focal_replication_or_original_study3_effect_is_extracted

### Priority 2 - api_candidate_b3869535651b5f0e

- Candidate: Eden, Daalmans, and Johnson (2017) -> Character morality, enjoyment, and appreciation: a replication of Eden, Daalmans, and Johnson (2017)
- Route/decision: `coverage_only` / `source_blocked_needs_value_bearing_article`
- Original: Eden, Daalmans, and Johnson (2017) ()
- Replication: Character morality, enjoyment, and appreciation: a replication of Eden, Daalmans, and Johnson (2017) (10.1080/15213269.2021.1884096)
- Source URLs: https://doi.org/10.1080/15213269.2021.1884096
- Local files already mirrored: data/raw/replication_projects/individual_auto_mining_blockers/api_candidate_b3869535651b5f0e/openalex_landing_page_url__10_1080_15213269_2021_1884096__osf_io__c1df7be23f68.html [html, 4190 bytes] | data/raw/replication_projects/individual_auto_mining_blockers/api_candidate_b3869535651b5f0e/openalex_landing_page_url__10_1080_15213269_2021_1884096__researchrepository_wvu_edu__b62ea57de8cc.html [html_or_xml, 34767 bytes]
- Known original support: none
- Known replication support: none
- Conversion/policy note: Do not promote from metadata alone. The batch found affirmative replication-language evidence, but did not mirror enough value-bearing source text for a matched original effect, original N, replication effect, and replication N under the current Figure 1 row policy.
- Task: manual_acquisition_or_repository_parse_if_prioritized

### Priority 2 - api_candidate_bb6c827070cfa1f7

- Candidate: Cockroach audience by task-difficulty social-facilitation interaction
- Route/decision: `coverage_only` / `not_row_original_effect_not_statistically_mapped`
- Original:  ()
- Replication:  ()
- Source URLs: none recorded
- Local files already mirrored: none
- Known original support: Search/PDF snippets identify original Zajonc et al. N = 40 for the critical 2 x 2 interaction, but also note the original article did not provide a clear statistical test of the central interaction.
- Known replication support: The replication article is source-blocked locally by SAGE 403 in this batch; search snippets report preregistered target N = 120 and a direct replication of the audience by task-difficulty claim.
- Conversion/policy note: Do not promote without a source-mapped original D/statistic for the central interaction; retain as a context/manual-acquisition lead.
- Task: manual_acquisition_if_interaction_effects_become_in_scope

### Priority 2 - api_candidate_ccd98d70dd2472bf

- Candidate: Krause Et Al. (2012) -> Mixed Evidence for Name Priming Effects as a Measure of Implicit Self-Esteem: A Conceptual Replication of Krause Et Al. (2012)
- Route/decision: `coverage_only` / `source_blocked_needs_value_bearing_article`
- Original: Krause Et Al. (2012) ()
- Replication: Mixed Evidence for Name Priming Effects as a Measure of Implicit Self-Esteem: A Conceptual Replication of Krause Et Al. (2012) (10.1521/soco.2021.39.5.591)
- Source URLs: https://doi.org/10.1521/soco.2021.39.5.591
- Local files already mirrored: data/raw/replication_projects/individual_auto_mining_blockers/api_candidate_ccd98d70dd2472bf/openalex_landing_page_url__10_1521_soco_2021_39_5_591__api_osf_io__8b5db1424b47.bin [json_like, 4284 bytes] | data/raw/replication_projects/individual_auto_mining_blockers/api_candidate_ccd98d70dd2472bf/openalex_landing_page_url__10_1521_soco_2021_39_5_591__osf_io__c1df7be23f68.html [html, 4190 bytes]
- Known original support: none
- Known replication support: none
- Conversion/policy note: Do not promote from metadata alone. The batch found affirmative replication-language evidence, but did not mirror enough value-bearing source text for a matched original effect, original N, replication effect, and replication N under the current Figure 1 row policy.
- Task: manual_acquisition_or_repository_parse_if_prioritized

### Priority 2 - api_candidate_ccea3138ba9e9efa

- Candidate: Study 1 of Rodeheffer et al. (2012) in Japan -> Resource scarcity priming and face perception: A preregistered conceptual replication of Study 1 of Rodeheffer et al. (2012) in Japan
- Route/decision: `coverage_only` / `source_blocked_conceptual_replication_needs_values`
- Original: Study 1 of Rodeheffer et al. (2012) in Japan ()
- Replication: Resource scarcity priming and face perception: A preregistered conceptual replication of Study 1 of Rodeheffer et al. (2012) in Japan (10.1016/j.cresp.2023.100169)
- Source URLs: https://doi.org/10.1016/j.cresp.2023.100169
- Local files already mirrored: data/raw/replication_projects/individual_search_batch006/api_candidate_ccea3138ba9e9efa/01_linkinghub_elsevier_com_retrieve_pii_s2666622723000825_e627c0c4e417.html [html, 2753 bytes] | data/raw/replication_projects/individual_auto_mining_blockers/api_candidate_ccea3138ba9e9efa/doi_resolver__10_1016_j_cresp_2023_100169__linkinghub_elsevier_com__e627c0c4e417.html [html, 2753 bytes] | data/raw/replication_projects/individual_auto_mining_blockers/api_candidate_ccea3138ba9e9efa/openalex_landing_page_url__10_1016_j_cresp_2023_100169__doaj_org__045ab68cf623.html [html_or_xml, 64580 bytes]
- Known original support: none
- Known replication support: none
- Conversion/policy note: Do not promote from metadata alone. The batch found affirmative replication-language evidence, but did not mirror enough value-bearing source text for a matched original effect, original N, replication effect, and replication N under the current Figure 1 row policy.
- Task: manual_acquisition_or_repository_parse_if_prioritized

### Priority 2 - api_candidate_d51bbeeeb3386937

- Candidate: the Criteria‐Based Content Analysis Condition in Bogaard Et al. (2014) -> Contextual Bias in Verbal Credibility Assessment: A Preregistered Direct Replication of the Criteria‐Based Content Analysis Condition in Bogaard Et al. (2014)
- Route/decision: `coverage_only` / `source_blocked_needs_value_bearing_article`
- Original: the Criteria‐Based Content Analysis Condition in Bogaard Et al. (2014) ()
- Replication: Contextual Bias in Verbal Credibility Assessment: A Preregistered Direct Replication of the Criteria‐Based Content Analysis Condition in Bogaard Et al. (2014) (10.1002/acp.70168)
- Source URLs: https://doi.org/10.1002/acp.70168
- Local files already mirrored: none
- Known original support: none
- Known replication support: none
- Conversion/policy note: Do not promote from metadata alone. The batch found affirmative replication-language evidence, but did not mirror enough value-bearing source text for a matched original effect, original N, replication effect, and replication N under the current Figure 1 row policy.
- Task: manual_acquisition_or_repository_parse_if_prioritized

### Priority 2 - api_candidate_d98523e0ce3e5e0d

- Candidate: Shen et al.'s (2019) Study on Online Image Credibility -> Contextual Changes, Credible Conclusions? A Direct and Conceptual Replication of Shen et al.'s (2019) Study on Online Image Credibility
- Route/decision: `coverage_only` / `source_blocked_needs_manual_acquisition`
- Original: Shen et al.'s (2019) Study on Online Image Credibility ()
- Replication: Contextual Changes, Credible Conclusions? A Direct and Conceptual Replication of Shen et al.'s (2019) Study on Online Image Credibility (10.1080/15213269.2025.2595452)
- Source URLs: https://doi.org/10.1080/15213269.2025.2595452
- Local files already mirrored: data/raw/replication_projects/individual_search_batch003/api_candidate_d98523e0ce3e5e0d/01_www_tandfonline_com_action_cookieabsent_26fcd1037997.html [html_or_xml, 105607 bytes] | data/raw/replication_projects/individual_auto_mining_blockers/api_candidate_d98523e0ce3e5e0d/embedded_pdf__1fd1aa8d293c__Contextual_Changes__Credible_Conclusions__A_Direct_and_Conceptual_Replication_of_Shen_et_al._s__2019__Study_on_Online_Image_Credibility.pdf [pdf, 16414 bytes] | data/raw/replication_projects/individual_auto_mining_blockers/api_candidate_d98523e0ce3e5e0d/embedded_pdf__8f881b5c8e48__Contextual_Changes__Credible_Conclusions__A_Direct_and_Conceptual_Replication_of_Shen_et_al._s__2019__Study_on_Online_Image_Credibility.pdf [pdf, 964418 bytes] | data/raw/replication_projects/individual_auto_mining_blockers/api_candidate_d98523e0ce3e5e0d/embedded_pdf__d75f00c30965__Contextual_Changes__Credible_Conclusions__A_Direct_and_Conceptual_Replication_of_Shen_et_al._s__2019__Study_on_Online_Image_Credibility.pdf [pdf, 1809 bytes] | data/raw/replication_projects/individual_auto_mining_blockers/api_candidate_d98523e0ce3e5e0d/openalex_landing_page_url__10_1080_15213269_2025_2595452__epub_ub_uni_muenchen_de__d405a57f2487.html [html_or_xml, 30536 bytes]
- Known original support: Mirrored Taylor & Francis acquisition artifact identifies the replication title but does not expose source values.
- Known replication support: The DOI landing route was metadata/cookie-page only locally in this batch.
- Conversion/policy note: Do not promote without article values and exact original target mapping.
- Task: Extract exact Shen online-image-credibility original and direct-replication effect/N values or classify as native-only/coverage-only.

### Priority 2 - api_candidate_f5027ea48e83c6e2

- Candidate: Darkness and dishonesty conceptual replication using coin toss task
- Route/decision: `coverage_only` / `not_row_conceptual_changed_task_original_effect_missing`
- Original:  ()
- Replication:  ()
- Source URLs: none recorded
- Local files already mirrored: data/raw/replication_projects/individual_search_batch004/api_candidate_f5027ea48e83c6e2/01_journals_plos_org_plosone_article_id_10_1371_journal_pone_0294484_b54c0aa73b72.html [html_or_xml, 159764 bytes]
- Known original support: Mirrored PLOS article identifies Zhong, Bohns, and Gino (2010) Experiment 1 as the original target but does not provide a matched original D/N effect for the coin-toss endpoint.
- Known replication support: Mirrored PLOS article reports final replication N = 102, dark-condition reported-score M = 5.96 SD = 1.48 versus light-condition M = 5.39 SD = 1.56, t(100) = 1.885, p = .031, Cohen's d = 0.374.
- Conversion/policy note: Do not promote because the replication changed the task from the original and the mirrored source does not expose the original matched effect size/N.
- Task: retain_as_context_source_until_original_effect_inputs_are_mirrored

### Priority 2 - api_candidate_f998e9bbe8b93e3b

- Candidate: the effectiveness of the cognitive interview -> An independent replication of the effectiveness of the cognitive interview
- Route/decision: `coverage_only` / `source_blocked_needs_value_bearing_article`
- Original: the effectiveness of the cognitive interview ()
- Replication: An independent replication of the effectiveness of the cognitive interview (10.1002/acp.2350050604)
- Source URLs: https://doi.org/10.1002/acp.2350050604
- Local files already mirrored: none
- Known original support: none
- Known replication support: none
- Conversion/policy note: Do not promote from metadata alone. The batch found affirmative replication-language evidence, but did not mirror enough value-bearing source text for a matched original effect, original N, replication effect, and replication N under the current Figure 1 row policy.
- Task: manual_acquisition_or_repository_parse_if_prioritized

### Priority 2 - api_candidate_fcdbe8ce78bf22a0

- Candidate: Schiller et al. (Nature, 2010) -> Registered Replication of Schiller et al. (Nature, 2010)
- Route/decision: `coverage_only` / `source_blocked_protocol_or_repository_only`
- Original: Schiller et al. (Nature, 2010) ()
- Replication: Registered Replication of Schiller et al. (Nature, 2010) (10.17605/osf.io/8chqu)
- Source URLs: https://doi.org/10.17605/osf.io/8chqu | https://osf.io/8chqu/ | 10.17605/osf.io/8chqu
- Local files already mirrored: data/raw/replication_projects/individual_search_batch006/api_candidate_fcdbe8ce78bf22a0/01_osf_io_8chqu_c1df7be23f68.html [html, 4190 bytes] | data/raw/replication_projects/individual_search_batch006/api_candidate_fcdbe8ce78bf22a0/02_osf_io_8chqu_c1df7be23f68.html [html, 4190 bytes] | data/raw/replication_projects/individual_search_batch006/api_candidate_fcdbe8ce78bf22a0/03_osf_io_8chqu_c1df7be23f68.html [html, 4190 bytes] | data/raw/replication_projects/individual_auto_mining_blockers/api_candidate_fcdbe8ce78bf22a0/doi_resolver__10_17605_osf_io_8chqu__osf_io__c1df7be23f68.html [html, 4190 bytes] | data/raw/replication_projects/individual_auto_mining_blockers/api_candidate_fcdbe8ce78bf22a0/openalex_landing_page_url__10_17605_osf_io_8chqu__api_osf_io__7d77fd3ba84a.bin [json_like, 4710 bytes] | data/raw/replication_projects/individual_auto_mining_blockers/api_candidate_fcdbe8ce78bf22a0/openalex_landing_page_url__10_17605_osf_io_8chqu__osf_io__c1df7be23f68.html [html, 4190 bytes] | data/raw/replication_projects/individual_auto_mining_blockers/api_candidate_fcdbe8ce78bf22a0/openalex_oa_url__10_17605_osf_io_8chqu__osf_io__c1df7be23f68.html [html, 4190 bytes]
- Known original support: Triage resolved the target as Schiller et al. (Nature, 2010).
- Known replication support: The routed DOI is an OSF registration/package record and duplicates the Schiller registration family.
- Conversion/policy note: Duplicate OSF registration/source-package hit for the Schiller replication family; no completed value-bearing source was resolved in this batch.
- Task: resolve_completed_replication_article_or_results_package_before_value_extraction
