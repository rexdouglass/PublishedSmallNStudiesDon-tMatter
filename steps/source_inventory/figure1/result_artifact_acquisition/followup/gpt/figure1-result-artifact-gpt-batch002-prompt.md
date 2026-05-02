# Figure 1 Result-Artifact Resolution: batch002

We are building a reproducible provenance pipeline for a plot of original-vs-replication/follow-up result pairs.

For each item below, research whether the lead has a reusable result-bearing artifact for Figure 1. A valid artifact can be a dataset, database export, workbook, CSV/TSV, code/data repository, supplement table, PDF/HTML table, API snapshot, or source-family file inventory that enumerates original-replication/follow-up result rows. Do not promote ordinary one-paper "replication package" material unless it actually reports an independent replication/follow-up result or contains a multi-row source-family table.

Return machine-readable JSON only with this shape:

```json
{
  "batch_id": "batch002",
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
    "followup_id": "result_artifact_followup_c848d848367d2a93",
    "corpus_database_id": "biblio_search_europepmc_2288d4a489a5",
    "name": "Meta-regression to explain shrinkage and heterogeneity in large-scale replication projects.",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.1371/journal.pone.0327799",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article route still needs data/supplement/source-object research"
  },
  {
    "followup_id": "result_artifact_followup_f3059509ca3f2126",
    "corpus_database_id": "biblio_search_europepmc_ab974cf9ef23",
    "name": "Metascientific replication project with the advanced meta-experimental protocol of the transparent psi project procedures for testing the precognitive effect claimed by Bem.",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.1371/journal.pone.0335330",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article_route_no_downloadable_result_artifact_found"
  },
  {
    "followup_id": "result_artifact_followup_2317fb97073fd2ea",
    "corpus_database_id": "biblio_search_crossref_87bab505c18a",
    "name": "Nanoscience is latest discipline to embrace large-scale replication efforts",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.1038/d41586-026-00439-6",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article route still needs data/supplement/source-object research"
  },
  {
    "followup_id": "result_artifact_followup_6e10941b3f4744d0",
    "corpus_database_id": "biblio_search_openalex_4cc77f01fc8b",
    "name": "Predicting replicability—Analysis of survey and prediction market data from large-scale forecasting projects",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.1371/journal.pone.0248780",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article_route_no_downloadable_result_artifact_found"
  },
  {
    "followup_id": "result_artifact_followup_f8c779f3e1c97070",
    "corpus_database_id": "domain_search_openalex_2481753d43b5",
    "name": "Predicting the replicability of social science lab experiments",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.1371/journal.pone.0225826",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article_route_no_downloadable_result_artifact_found"
  },
  {
    "followup_id": "result_artifact_followup_801bb914788853b4",
    "corpus_database_id": "citation_search_openalex_cites_f3b6a5ee39eb",
    "name": "Preprint - Meta-Analyzing the Multiverse: A Peek Under the Hood of Selective Reporting",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.31234/osf.io/43yae",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article_route_no_downloadable_result_artifact_found"
  },
  {
    "followup_id": "result_artifact_followup_ce43bfa6f24636e2",
    "corpus_database_id": "biblio_search_crossref_abffc2adc22f",
    "name": "Pupil Size and Intelligence: A Large-Scale Replication Study",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.46469/mq.2020.60.4.5",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article route still needs data/supplement/source-object research"
  },
  {
    "followup_id": "result_artifact_followup_17914d555b0ba997",
    "corpus_database_id": "biblio_search_europepmc_bc6a68fdf4d6",
    "name": "Reflections on Conducting a Large Replication Project in Sports and Exercise Science.",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.1007/s40279-025-02200-x",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article route still needs data/supplement/source-object research"
  },
  {
    "followup_id": "result_artifact_followup_64352b17b5c3816c",
    "corpus_database_id": "citation_search_crossref_93a1da3f64d9",
    "name": "Registered report: Coadministration of a tumor-penetrating peptide enhances the efficacy of cancer drugs",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.7554/elife.06959",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article route still needs data/supplement/source-object research"
  },
  {
    "followup_id": "result_artifact_followup_216db0ef54c235f6",
    "corpus_database_id": "citation_search_crossref_b74f4d7ba088",
    "name": "Registered report: Discovery and preclinical validation of drug indications using compendia of public gene expression data",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.7554/elife.06847",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article route still needs data/supplement/source-object research"
  },
  {
    "followup_id": "result_artifact_followup_4fd914fbdfec04b8",
    "corpus_database_id": "citation_search_crossref_14e2aa0a32fe",
    "name": "Registered report: Intestinal inflammation targets cancer-inducing activity of the microbiota",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.7554/elife.04186",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article route still needs data/supplement/source-object research"
  },
  {
    "followup_id": "result_artifact_followup_c7f304c109362640",
    "corpus_database_id": "citation_search_crossref_6122fb3dbcbf",
    "name": "Registered report: Melanoma genome sequencing reveals frequent PREX2 mutations",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.7554/elife.04180",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article route still needs data/supplement/source-object research"
  },
  {
    "followup_id": "result_artifact_followup_a2129fb1f375c436",
    "corpus_database_id": "citation_search_crossref_bf4b0584a2c7",
    "name": "Registered report: Senescence surveillance of pre-malignant hepatocytes limits liver cancer development",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.7554/elife.04105",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article route still needs data/supplement/source-object research"
  },
  {
    "followup_id": "result_artifact_followup_e1c236bafcce742d",
    "corpus_database_id": "citation_search_crossref_9ba03598b302",
    "name": "Registered report: Systematic identification of genomic markers of drug sensitivity in cancer cells",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.7554/elife.13620",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article route still needs data/supplement/source-object research"
  },
  {
    "followup_id": "result_artifact_followup_e6bea4a55de4390a",
    "corpus_database_id": "biblio_search_openalex_dc5b3694c618",
    "name": "Replicability, Robustness, and Reproducibility in Psychological Science",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.1146/annurev-psych-020821-114157 | https://doi.org/10.31234/osf.io/ksfvq",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article_route_no_downloadable_result_artifact_found"
  },
  {
    "followup_id": "result_artifact_followup_f3cba32f09e56473",
    "corpus_database_id": "citation_search_crossref_2f6361267644",
    "name": "Replication Study: BET bromodomain inhibition as a therapeutic strategy to target c-Myc",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.7554/elife.21253",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article route still needs data/supplement/source-object research"
  },
  {
    "followup_id": "result_artifact_followup_8cff30aab4f1c864",
    "corpus_database_id": "citation_search_crossref_a3de159f7a03",
    "name": "Replication Study: Coadministration of a tumor-penetrating peptide enhances the efficacy of cancer drugs",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.7554/elife.17584",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article route still needs data/supplement/source-object research"
  },
  {
    "followup_id": "result_artifact_followup_db889f38be424fcb",
    "corpus_database_id": "citation_search_crossref_db938c1a600f",
    "name": "Replication Study: Discovery and preclinical validation of drug indications using compendia of public gene expression data",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.7554/elife.17044",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article route still needs data/supplement/source-object research"
  },
  {
    "followup_id": "result_artifact_followup_ddd77aca6199278f",
    "corpus_database_id": "citation_search_crossref_1296a0e46d85",
    "name": "Replication Study: Melanoma genome sequencing reveals frequent PREX2 mutations",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.7554/elife.21634",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article route still needs data/supplement/source-object research"
  },
  {
    "followup_id": "result_artifact_followup_7e3b1654c0fb9138",
    "corpus_database_id": "citation_search_crossref_53c2ae83b22f",
    "name": "Replication Study: The CD47-signal regulatory protein alpha (SIRPa) interaction is a therapeutic target for human solid tumors",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.7554/elife.18173",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article route still needs data/supplement/source-object research"
  },
  {
    "followup_id": "result_artifact_followup_64ae68a9d7efaea6",
    "corpus_database_id": "citation_search_openalex_417812a7d65b",
    "name": "Replication concerns in sports and exercise science: a narrative review of selected methodological issues in the field",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.1098/rsos.220946",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article_route_no_downloadable_result_artifact_found"
  },
  {
    "followup_id": "result_artifact_followup_4fa6481f15884428",
    "corpus_database_id": "biblio_search_europepmc_19dcd494fa29",
    "name": "Replication of null results: Absence of evidence or evidence of absence?",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.7554/elife.92311",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article route still needs data/supplement/source-object research"
  },
  {
    "followup_id": "result_artifact_followup_32b977a94300607e",
    "corpus_database_id": "citation_search_openalex_5b83c7863834",
    "name": "Statistical methods for replicability assessment",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.1214/20-aoas1336",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article_route_no_downloadable_result_artifact_found"
  },
  {
    "followup_id": "result_artifact_followup_8f70af27091f06c0",
    "corpus_database_id": "biblio_search_openalex_fa42728a0892",
    "name": "Successes and Failures of Replications: A Meta-Analysis of Independent Replication Studies Based on the OSF Registries",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.31222/osf.io/8psw2",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article_route_no_downloadable_result_artifact_found"
  },
  {
    "followup_id": "result_artifact_followup_c6dfe84310fc6351",
    "corpus_database_id": "biblio_search_crossref_444567d7cff3",
    "name": "The Effect of Replications on Citation Patterns: Evidence From a Large-Scale Reproducibility Project",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.1177/09567976211005767",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article_route_no_downloadable_result_artifact_found"
  },
  {
    "followup_id": "result_artifact_followup_9ea8420d18e72f30",
    "corpus_database_id": "biblio_search_europepmc_5a5defc59a7e",
    "name": "The Replication Database: Documenting the Replicability of Psychological Science.",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.5334/jopd.101 | https://doi.org/10.31222/osf.io/me2ub",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article_route_no_downloadable_result_artifact_found"
  },
  {
    "followup_id": "result_artifact_followup_a69323210de86cea",
    "corpus_database_id": "citation_search_crossref_320216629369",
    "name": "The Representativeness Heuristic Revisited: Registered Replication Report of Kahneman and Tversky (1973)",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.24072/pci.rr.100609",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article route still needs data/supplement/source-object research"
  },
  {
    "followup_id": "result_artifact_followup_439d0a7c8c65980e",
    "corpus_database_id": "biblio_search_crossref_be5b37ea07db",
    "name": "The Reproducibility Project: A Model of Large-Scale Collaboration for Empirical Research on Reproducibility",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.2139/ssrn.2195999",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article_route_no_downloadable_result_artifact_found"
  },
  {
    "followup_id": "result_artifact_followup_17486b83ecb4f6cc",
    "corpus_database_id": "biblio_search_openalex_f70bd4f4b390",
    "name": "The Reverse Journal v5.0: Pre-Experiment Risk Intelligence Engine",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.5281/zenodo.19057339",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article route still needs data/supplement/source-object research"
  },
  {
    "followup_id": "result_artifact_followup_e1229863ba056db7",
    "corpus_database_id": "biblio_search_europepmc_3e6d6755ad19",
    "name": "The assessment of replicability using the sum of <i>p</i>-values.",
    "record_kind": "candidate_corpus_or_database",
    "priority": "high",
    "route": "article_pdf_supplement_or_data_availability_route",
    "host": "doi.org",
    "landing_url": "https://doi.org/10.1098/rsos.240149",
    "raw_url": "",
    "question": "Does this lead have a reusable Figure 1 result-bearing source artifact (dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject.",
    "reason": "article_route_no_downloadable_result_artifact_found"
  }
]
```
