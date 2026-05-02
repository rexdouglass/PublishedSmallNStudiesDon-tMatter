# Figure 1 Result-Artifact Resolution: batch001

We are building a reproducible provenance pipeline for a plot of original-vs-replication/follow-up result pairs.

For each item below, research whether the lead has a reusable result-bearing artifact for Figure 1. A valid artifact can be a dataset, database export, workbook, CSV/TSV, code/data repository, supplement table, PDF/HTML table, API snapshot, or source-family file inventory that enumerates original-replication/follow-up result rows. Do not promote ordinary one-paper "replication package" material unless it actually reports an independent replication/follow-up result or contains a multi-row source-family table.

Return machine-readable JSON only with this shape:

```json
{
  "batch_id": "batch001",
  "decisions": [
    {
      "followup_id": "...",
      "corpus_database_id": "...",
      "decision": "artifact_found | no_public_artifact_found | individual_paper_only | context_only | duplicate | reject_not_figure1 | needs_user_manual_access",
      "result_artifact_urls": ["..."],
      "result_artifact_file_names": ["..."],
      "source_family_url": "...",
      "publication_or_project_doi": "...",
      "classification_reason": "...",
      "recommended_next_action": "...",
      "confidence": "high | medium | low",
      "sources_checked": ["..."]
    }
  ]
}
```

Items:

```json
[
  {
    "followup_id": "result_artifact_followup_57895536b878b4ce",
    "corpus_database_id": "citation_search_openalex_1fc3e15ca54b",
    "name": "A Multilab Preregistered Replication of the Ego-Depletion Effect",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.1177/1745691616652873",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article_route_no_downloadable_result_artifact_found"
  },
  {
    "followup_id": "result_artifact_followup_53325f2962bd4455",
    "corpus_database_id": "biblio_search_europepmc_e157ba24e5e8",
    "name": "A Problem in Theory and More: Measuring the Moderating Role of Culture in Many Labs 2",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.31234/osf.io/hmnrx",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article_route_no_downloadable_result_artifact_found"
  },
  {
    "followup_id": "result_artifact_followup_966573057a3ce2ca",
    "corpus_database_id": "biblio_search_europepmc_73a746f8d5ae",
    "name": "A large-scale in silico replication of ecological and evolutionary studies.",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.1038/s41559-024-02530-5",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article route still needs data/supplement/source-object research"
  },
  {
    "followup_id": "result_artifact_followup_220ab9f45a58f62f",
    "corpus_database_id": "biblio_search_europepmc_62ed5748b3a7",
    "name": "A scoping review on metrics to quantify reproducibility: a multitude of questions leads to a multitude of metrics.",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.1098/rsos.242076",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article_route_no_downloadable_result_artifact_found"
  },
  {
    "followup_id": "result_artifact_followup_400dbe4a9c60169f",
    "corpus_database_id": "biblio_search_europepmc_13a3032c9195",
    "name": "Absence of a meaningful effect of intranasal oxytocin on trusting behavior: a registered report with pooled equivalence testing.",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.1016/j.cortex.2026.03.006",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article_route_no_downloadable_result_artifact_found"
  },
  {
    "followup_id": "result_artifact_followup_da0d68f8b026ff42",
    "corpus_database_id": "biblio_search_crossref_95b2c7981ea2",
    "name": "Administering a victim impact curriculum to inmates: a multi-site replication",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.1080/1478601x.2015.1014037",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article_route_no_downloadable_result_artifact_found"
  },
  {
    "followup_id": "result_artifact_followup_9f5d5c48606c4f7d",
    "corpus_database_id": "citation_search_openalex_c8d6e1d0dbe0",
    "name": "An open investigation of the reproducibility of cancer biology research",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.7554/elife.04333",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article route still needs data/supplement/source-object research"
  },
  {
    "followup_id": "result_artifact_followup_48c70647bbd45397",
    "corpus_database_id": "biblio_search_openalex_5e106b038595",
    "name": "Analysis of rare Parkinson’s disease variants in millions of people",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.1038/s41531-023-00608-8",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article route still needs data/supplement/source-object research"
  },
  {
    "followup_id": "result_artifact_followup_06e7907fca8e9494",
    "corpus_database_id": "citation_search_openalex_166831ec4722",
    "name": "Analyzing Data of a Multilab Replication Project With Individual Participant Data Meta-Analysis",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.1027/2151-2604/a000483",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article_route_no_downloadable_result_artifact_found"
  },
  {
    "followup_id": "result_artifact_followup_916db12ab3f068e9",
    "corpus_database_id": "citation_search_openalex_8205f5f8a5c7",
    "name": "Analyzing data of a multilab replication project with individual participant data meta-analysis: A tutorial",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.31222/osf.io/9tmua",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article_route_no_downloadable_result_artifact_found"
  },
  {
    "followup_id": "result_artifact_followup_51345b4c55bd569b",
    "corpus_database_id": "citation_search_openalex_721d17ae7904",
    "name": "Artificial intelligence in psychology research",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.31234/osf.io/rva3w",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article_route_no_downloadable_result_artifact_found"
  },
  {
    "followup_id": "result_artifact_followup_fde5f6ffc521eab1",
    "corpus_database_id": "biblio_search_openalex_0dc003705bb2",
    "name": "Can cancer researchers accurately judge whether preclinical reports will reproduce?",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.1371/journal.pbio.2002212",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article_route_no_downloadable_result_artifact_found"
  },
  {
    "followup_id": "result_artifact_followup_06feecb063ebc58d",
    "corpus_database_id": "biblio_search_crossref_b5e8a315b055",
    "name": "Cancer reproducibility project scales back ambitions",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.1038/nature.2015.18938",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article route still needs data/supplement/source-object research"
  },
  {
    "followup_id": "result_artifact_followup_439fb0c7f8c073fb",
    "corpus_database_id": "citation_search_openalex_e00e4206ad4b",
    "name": "Confounds in “failed” replications",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.31234/osf.io/gth8u",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article_route_no_downloadable_result_artifact_found"
  },
  {
    "followup_id": "result_artifact_followup_2c170d45f923c83d",
    "corpus_database_id": "biblio_search_europepmc_c341f9196f7e",
    "name": "Cross-platform metabolomics imputation using importance-weighted autoencoders",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.1101/2025.03.06.25323475 | https://doi.org/10.1038/s41540-025-00644-5",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article_route_no_downloadable_result_artifact_found"
  },
  {
    "followup_id": "result_artifact_followup_270a0a129c1366d0",
    "corpus_database_id": "citation_search_openalex_67155624c5f2",
    "name": "Data from Investigating Variation in Replicability: A “Many Labs” Replication Project",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.5334/jopd.ad | https://doi.org/10.31234/osf.io/25ju4",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article_route_no_downloadable_result_artifact_found"
  },
  {
    "followup_id": "result_artifact_followup_7fc47685ada3096e",
    "corpus_database_id": "citation_search_crossref_35667e3741ca",
    "name": "Does expertise matter in replication? An examination of the reproducibility project: Psychology",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.1016/j.jesp.2016.07.003",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article_route_no_downloadable_result_artifact_found"
  },
  {
    "followup_id": "result_artifact_followup_145e86fd662532eb",
    "corpus_database_id": "biblio_search_europepmc_4c109c902f6f",
    "name": "Eleven years of student replication projects provide evidence on the correlates of replicability in psychology.",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.1098/rsos.231240",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article_route_no_downloadable_result_artifact_found"
  },
  {
    "followup_id": "result_artifact_followup_90779bb24435c629",
    "corpus_database_id": "biblio_search_europepmc_f4494de3204c",
    "name": "Estimating the Replicability of Sports and Exercise Science Research.",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.1007/s40279-025-02201-w",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article route still needs data/supplement/source-object research"
  },
  {
    "followup_id": "result_artifact_followup_2446c80658db8f70",
    "corpus_database_id": "biblio_search_europepmc_5fee7a46d6f5",
    "name": "Evaluating meta-analysis as a replication success measure.",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.1371/journal.pone.0308495",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article_route_no_downloadable_result_artifact_found"
  },
  {
    "followup_id": "result_artifact_followup_fd079fd93e4a7d2e",
    "corpus_database_id": "biblio_search_europepmc_c1d8b918289a",
    "name": "Evidence for Infant-directed Speech Preference Is Consistent Across Large-scale, Multi-site Replication and Meta-analysis.",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.1162/opmi_a_00134",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article route still needs data/supplement/source-object research"
  },
  {
    "followup_id": "result_artifact_followup_e0459aa64a44bc9b",
    "corpus_database_id": "biblio_search_europepmc_1e8b61f37a9f",
    "name": "Examining the replicability of online experiments selected by a decision market.",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.1038/s41562-024-02062-9",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article route still needs data/supplement/source-object research"
  },
  {
    "followup_id": "result_artifact_followup_f69c83d476fe8395",
    "corpus_database_id": "domain_search_openalex_176565dc87a1",
    "name": "Heterogeneity in direct replications in psychology and its association with effect size.",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.1037/bul0000294",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article route still needs data/supplement/source-object research"
  },
  {
    "followup_id": "result_artifact_followup_99f686bc87c3c5da",
    "corpus_database_id": "citation_search_openalex_6c09c03f429d",
    "name": "How Replicable Are Links Between Personality Traits and Consequential Life Outcomes? The Life Outcomes of Personality Replication Project",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.1177/0956797619831612",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article_route_no_downloadable_result_artifact_found"
  },
  {
    "followup_id": "result_artifact_followup_867768082be7fd2f",
    "corpus_database_id": "biblio_search_europepmc_85a68784cd0c",
    "name": "Investigating the replicability of preclinical cancer biology.",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.7554/elife.71601",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article route still needs data/supplement/source-object research"
  },
  {
    "followup_id": "result_artifact_followup_ec531c73835e65e9",
    "corpus_database_id": "citation_search_openalex_e52d1ffa1221",
    "name": "Many Labs 2: Investigating Variation in Replicability Across Samples and Settings",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.1177/2515245918810225",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article_route_no_downloadable_result_artifact_found"
  },
  {
    "followup_id": "result_artifact_followup_1c8bfff71c0d5fa5",
    "corpus_database_id": "citation_search_crossref_f9ca11ca4cfc",
    "name": "Many Labs 5: Registered Replication of LoBue and DeLoache (2008)",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.1177/2515245920953350",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article_route_no_downloadable_result_artifact_found"
  },
  {
    "followup_id": "result_artifact_followup_1d9742d3f0854ead",
    "corpus_database_id": "biblio_search_openalex_1c502db683ac",
    "name": "Many Labs 5: Testing Pre-Data-Collection Peer Review as an Intervention to Increase Replicability",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.1177/2515245920958687",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article_route_no_downloadable_result_artifact_found"
  },
  {
    "followup_id": "result_artifact_followup_6fd880728dcc13c7",
    "corpus_database_id": "citation_search_openalex_8dc2c2e8bc8e",
    "name": "Meta-Analysis",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.4324/9781351137713-22",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article_route_no_downloadable_result_artifact_found"
  },
  {
    "followup_id": "result_artifact_followup_5f3435836b1a79ab",
    "corpus_database_id": "citation_search_openalex_cites_7c2996716eed",
    "name": "Meta-analyzing the multiverse: A peek under the hood of selective reporting.",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.1037/met0000559",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article route still needs data/supplement/source-object research"
  }
]
```
