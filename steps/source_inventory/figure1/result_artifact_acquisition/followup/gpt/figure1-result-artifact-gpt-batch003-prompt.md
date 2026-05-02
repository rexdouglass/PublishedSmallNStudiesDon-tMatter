# Figure 1 Result-Artifact Resolution: batch003

We are building a reproducible provenance pipeline for a plot of original-vs-replication/follow-up result pairs.

For each item below, research whether the lead has a reusable result-bearing artifact for Figure 1. A valid artifact can be a dataset, database export, workbook, CSV/TSV, code/data repository, supplement table, PDF/HTML table, API snapshot, or source-family file inventory that enumerates original-replication/follow-up result rows. Do not promote ordinary one-paper "replication package" material unless it actually reports an independent replication/follow-up result or contains a multi-row source-family table.

Return machine-readable JSON only with this shape:

```json
{
  "batch_id": "batch003",
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
    "followup_id": "result_artifact_followup_9ef05b9decb659b9",
    "corpus_database_id": "citation_search_crossref_6247e94906e6",
    "name": "The production log: A digital imaging capacity replication project",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.69554/frlp6710",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article route still needs data/supplement/source-object research"
  },
  {
    "followup_id": "result_artifact_followup_db75b851c693c255",
    "corpus_database_id": "citation_search_openalex_cites_07c3f155eb86",
    "name": "The replication crisis has led to positive structural, procedural, and community changes",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.1038/s44271-023-00003-2 | https://doi.org/10.31222/osf.io/r6cvx",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article route still needs data/supplement/source-object research"
  },
  {
    "followup_id": "result_artifact_followup_ac65ca5cc4c6f0c4",
    "corpus_database_id": "citation_search_openalex_cites_f77d0173ee75",
    "name": "Time to adjust: Improving replicability in experimental psychology by adjustment for evident selective inference",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.48550/arxiv.2006.11585",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article_route_no_downloadable_result_artifact_found"
  },
  {
    "followup_id": "result_artifact_followup_6b5cfaf7f9f3a596",
    "corpus_database_id": "registry_search_europepmc_bb12dc539169",
    "name": "Triplett’s Social Facilitation Experiment: A Registered Replication Report",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.31234/osf.io/bqzj9_v1",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article_route_no_downloadable_result_artifact_found"
  },
  {
    "followup_id": "result_artifact_followup_6652cbf8ce359c77",
    "corpus_database_id": "biblio_search_europepmc_e06fd719c585",
    "name": "Unstable Measures, Unreliable Effects: Re-evaluating Replicability with Reliability Informed Confidence Intervals",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.21203/rs.3.rs-5937985/v1",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article route still needs data/supplement/source-object research"
  },
  {
    "followup_id": "result_artifact_followup_97b1457955721a1d",
    "corpus_database_id": "citation_search_openalex_63df894f37fe",
    "name": "Updating the guidelines for data transparency in the British Journal of Pharmacology – data sharing and the use of scatter plots instead of bar charts",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.1111/bph.13925",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article_route_no_downloadable_result_artifact_found"
  },
  {
    "followup_id": "result_artifact_followup_903366c084a3c284",
    "corpus_database_id": "biblio_search_openalex_da504593e056",
    "name": "Using model-based predictions to inform the mathematical aggregation of human-based predictions of replicability",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.31222/osf.io/f675q",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article_route_no_downloadable_result_artifact_found"
  },
  {
    "followup_id": "result_artifact_followup_c52e2f53a1e7aa06",
    "corpus_database_id": "biblio_search_crossref_447554bdc098",
    "name": "Visual and behavioral responses to social and non-social threats: A multi-site replication",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.1016/j.actpsy.2024.104612",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article_route_no_downloadable_result_artifact_found"
  },
  {
    "followup_id": "result_artifact_followup_5bf7f467ccb13dc2",
    "corpus_database_id": "biblio_search_openalex_de35e9f48ef6",
    "name": "Would Ecology Fail the Repeatability Test?",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.1093/biosci/biv176",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article route still needs data/supplement/source-object research"
  },
  {
    "followup_id": "result_artifact_followup_f9dd0fb50949f488",
    "corpus_database_id": "corpus_db_doyen_et_al_2012_article_manual",
    "name": "Doyen et al. 2012 article (manual)",
    "record_kind": "replication_project",
    "priority": "medium",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "",
    "landing_url": "",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article_route_no_downloadable_result_artifact_found"
  },
  {
    "followup_id": "result_artifact_followup_a8656ee632c96fff",
    "corpus_database_id": "corpus_db_rpp_project_record_alias_manual",
    "name": "RPP project record alias (manual)",
    "record_kind": "replication_project",
    "priority": "medium",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "",
    "landing_url": "",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article_route_no_downloadable_result_artifact_found"
  },
  {
    "followup_id": "result_artifact_followup_6ace24fdce856419",
    "corpus_database_id": "corpus_db_rrr_alogna_2014_manual",
    "name": "RRR Alogna 2014 (manual)",
    "record_kind": "replication_project",
    "priority": "medium",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "",
    "landing_url": "",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article_route_no_downloadable_result_artifact_found"
  }
]
```
