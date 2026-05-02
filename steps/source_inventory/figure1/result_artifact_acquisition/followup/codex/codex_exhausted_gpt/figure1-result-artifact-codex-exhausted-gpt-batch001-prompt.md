# Figure 1 Codex-Exhausted Result-Artifact Resolution: batch001

Codex has already run deterministic provider/direct acquisition and mirror/sample attempts for these rows. Do not repeat generic search blindly. For each item, identify a concrete reusable result-bearing artifact if one exists, or explain why the public route appears unavailable.

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
    "followup_id": "result_artifact_followup_d50bce80522bbbac",
    "corpus_database_id": "repo_search_osf_de5a21118204",
    "name": "A multi-site Registered Replication Report of Olson &amp; Fazio (2001) \"Implicit Attitude Formation Through Classical Conditioning\"",
    "previous_codex_decision": "deterministic_repair_exhausted",
    "decision_basis": "osf_inventory:no_files_found:3hjpf:failed:{\"errors\":[{\"detail\":\"Not found.\"}],\"meta\":{\"version\":\"2.0\"}} | files=0",
    "landing_url": "https://osf.io/3hjpf/",
    "raw_url": "",
    "question": "Codex deterministic provider/direct repair did not find a public local result artifact. Research whether this lead has a reusable Figure 1 result-bearing artifact (dataset, workbook, source-family table, supplement, repository, PDF/HTML table, or file inventory), or classify it as individual_paper_only, context_only, duplicate, reject_not_figure1, or no_public_artifact_found."
  },
  {
    "followup_id": "result_artifact_followup_52934b30ab540397",
    "corpus_database_id": "repo_search_datacite_6abf8205297e",
    "name": "Combining specific task-oriented training with manual therapy to improve balance and mobility in patients after stroke: a mixed methods pilot randomised controlled trial",
    "previous_codex_decision": "deterministic_repair_exhausted",
    "decision_basis": "figshare_inventory:failed:no_figshare_article_id",
    "landing_url": "https://tandf.figshare.com/articles/dataset/Combining_specific_task-oriented_training_with_manual_therapy_to_improve_balance_and_mobility_in_patients_after_stroke_a_mixed_methods_pilot_randomised_controlled_trial/22598456/1 | https://tandf.figshare.com/articles/dataset/Combining_specific_task-oriented_training_with_manual_therapy_to_improve_balance_and_mobility_in_patients_after_stroke_a_mixed_methods_pilot_randomised_controlled_trial/22598456",
    "raw_url": "",
    "question": "Codex deterministic provider/direct repair did not find a public local result artifact. Research whether this lead has a reusable Figure 1 result-bearing artifact (dataset, workbook, source-family table, supplement, repository, PDF/HTML table, or file inventory), or classify it as individual_paper_only, context_only, duplicate, reject_not_figure1, or no_public_artifact_found."
  },
  {
    "followup_id": "result_artifact_followup_c9b8c2edac3f27fa",
    "corpus_database_id": "repo_search_osf_59c938bcdc36",
    "name": "Direct replications in the era of open sampling",
    "previous_codex_decision": "deterministic_repair_exhausted",
    "decision_basis": "osf_inventory:no_files_found:x2gfc:providers=1 | files=0",
    "landing_url": "https://osf.io/x2gfc/",
    "raw_url": "",
    "question": "Codex deterministic provider/direct repair did not find a public local result artifact. Research whether this lead has a reusable Figure 1 result-bearing artifact (dataset, workbook, source-family table, supplement, repository, PDF/HTML table, or file inventory), or classify it as individual_paper_only, context_only, duplicate, reject_not_figure1, or no_public_artifact_found."
  },
  {
    "followup_id": "result_artifact_followup_7a2b51377f4c2574",
    "corpus_database_id": "repo_search_osf_fdacffa906b9",
    "name": "Headspace for Parents: A Pilot Randomised Controlled Trial",
    "previous_codex_decision": "deterministic_repair_exhausted",
    "decision_basis": "osf_inventory:no_files_found:63av8:failed:{\"errors\":[{\"detail\":\"Not found.\"}],\"meta\":{\"version\":\"2.0\"}} | files=0",
    "landing_url": "https://osf.io/63av8/",
    "raw_url": "",
    "question": "Codex deterministic provider/direct repair did not find a public local result artifact. Research whether this lead has a reusable Figure 1 result-bearing artifact (dataset, workbook, source-family table, supplement, repository, PDF/HTML table, or file inventory), or classify it as individual_paper_only, context_only, duplicate, reject_not_figure1, or no_public_artifact_found."
  },
  {
    "followup_id": "result_artifact_followup_2adc26de8c0f37ab",
    "corpus_database_id": "repo_search_osf_038ad61f41bb",
    "name": "Incidental Attitude Formation via the Surveillance Task: A Multi-Site Registered Replication Report of Olson and Fazio (2001) \"Implicit Attitude Formation Through Classical Conditioning\"",
    "previous_codex_decision": "deterministic_repair_exhausted",
    "decision_basis": "osf_inventory:no_files_found:xqv8b:failed:{\"errors\":[{\"detail\":\"Not found.\"}],\"meta\":{\"version\":\"2.0\"}} | files=0",
    "landing_url": "https://osf.io/xqv8b/",
    "raw_url": "",
    "question": "Codex deterministic provider/direct repair did not find a public local result artifact. Research whether this lead has a reusable Figure 1 result-bearing artifact (dataset, workbook, source-family table, supplement, repository, PDF/HTML table, or file inventory), or classify it as individual_paper_only, context_only, duplicate, reject_not_figure1, or no_public_artifact_found."
  },
  {
    "followup_id": "result_artifact_followup_4f3c39fbc7ccbf6f",
    "corpus_database_id": "domain_search_osf_523739d259cc",
    "name": "Management Science Reproducibility Project",
    "previous_codex_decision": "deterministic_repair_exhausted",
    "decision_basis": "osf_inventory:no_files_found:mjqg5:failed:{\"errors\":[{\"detail\":\"Not found.\"}],\"meta\":{\"version\":\"2.0\"}} | files=0",
    "landing_url": "https://osf.io/mjqg5/",
    "raw_url": "",
    "question": "Codex deterministic provider/direct repair did not find a public local result artifact. Research whether this lead has a reusable Figure 1 result-bearing artifact (dataset, workbook, source-family table, supplement, repository, PDF/HTML table, or file inventory), or classify it as individual_paper_only, context_only, duplicate, reject_not_figure1, or no_public_artifact_found."
  },
  {
    "followup_id": "result_artifact_followup_2babe5ca55ea9895",
    "corpus_database_id": "repo_search_osf_c75edd0dddf4",
    "name": "Mastroianni_2023 Replication Project",
    "previous_codex_decision": "deterministic_repair_exhausted",
    "decision_basis": "osf_inventory:no_files_found:bt58q:failed:{\"errors\":[{\"detail\":\"Not found.\"}],\"meta\":{\"version\":\"2.0\"}} | files=0",
    "landing_url": "https://osf.io/bt58q/",
    "raw_url": "",
    "question": "Codex deterministic provider/direct repair did not find a public local result artifact. Research whether this lead has a reusable Figure 1 result-bearing artifact (dataset, workbook, source-family table, supplement, repository, PDF/HTML table, or file inventory), or classify it as individual_paper_only, context_only, duplicate, reject_not_figure1, or no_public_artifact_found."
  },
  {
    "followup_id": "result_artifact_followup_744375c528aebaea",
    "corpus_database_id": "repo_search_osf_aabadb891e8b",
    "name": "Preregistration: Literature Search - Replication studies and original studies",
    "previous_codex_decision": "deterministic_repair_exhausted",
    "decision_basis": "osf_inventory:no_files_found:dsqep:failed:{\"errors\":[{\"detail\":\"Not found.\"}],\"meta\":{\"version\":\"2.0\"}} | files=0",
    "landing_url": "https://osf.io/dsqep/",
    "raw_url": "",
    "question": "Codex deterministic provider/direct repair did not find a public local result artifact. Research whether this lead has a reusable Figure 1 result-bearing artifact (dataset, workbook, source-family table, supplement, repository, PDF/HTML table, or file inventory), or classify it as individual_paper_only, context_only, duplicate, reject_not_figure1, or no_public_artifact_found."
  },
  {
    "followup_id": "result_artifact_followup_da0046b5d3881aed",
    "corpus_database_id": "repo_search_datacite_6f6fbb02bbc4",
    "name": "Primary data and results",
    "previous_codex_decision": "deterministic_repair_exhausted",
    "decision_basis": "figshare_inventory:failed:no_figshare_article_id",
    "landing_url": "https://figshare.com/articles/dataset/Primary_data_and_results/31971444/1",
    "raw_url": "",
    "question": "Codex deterministic provider/direct repair did not find a public local result artifact. Research whether this lead has a reusable Figure 1 result-bearing artifact (dataset, workbook, source-family table, supplement, repository, PDF/HTML table, or file inventory), or classify it as individual_paper_only, context_only, duplicate, reject_not_figure1, or no_public_artifact_found."
  },
  {
    "followup_id": "result_artifact_followup_6571b8f058ec89a2",
    "corpus_database_id": "repo_search_osf_9925b7bbbb00",
    "name": "Recommender Systems Reproducibility Project",
    "previous_codex_decision": "deterministic_repair_exhausted",
    "decision_basis": "osf_inventory:no_files_found:yw84j:failed:{\"errors\":[{\"detail\":\"Not found.\"}],\"meta\":{\"version\":\"2.0\"}} | 8karz:failed:{\"errors\":[{\"detail\":\"Not found.\"}],\"meta\":{\"version\":\"2.0\"}} | files=0",
    "landing_url": "https://osf.io/yw84j/ | https://osf.io/8karz/",
    "raw_url": "",
    "question": "Codex deterministic provider/direct repair did not find a public local result artifact. Research whether this lead has a reusable Figure 1 result-bearing artifact (dataset, workbook, source-family table, supplement, repository, PDF/HTML table, or file inventory), or classify it as individual_paper_only, context_only, duplicate, reject_not_figure1, or no_public_artifact_found."
  },
  {
    "followup_id": "result_artifact_followup_0bb387588f1a25e8",
    "corpus_database_id": "repo_search_osf_fffdef2d8c78",
    "name": "Replication",
    "previous_codex_decision": "deterministic_repair_exhausted",
    "decision_basis": "osf_inventory:no_files_found:vpceb:failed:{\"errors\":[{\"detail\":\"Not found.\"}],\"meta\":{\"version\":\"2.0\"}} | files=0",
    "landing_url": "https://osf.io/vpceb/",
    "raw_url": "",
    "question": "Codex deterministic provider/direct repair did not find a public local result artifact. Research whether this lead has a reusable Figure 1 result-bearing artifact (dataset, workbook, source-family table, supplement, repository, PDF/HTML table, or file inventory), or classify it as individual_paper_only, context_only, duplicate, reject_not_figure1, or no_public_artifact_found."
  },
  {
    "followup_id": "result_artifact_followup_80281b4c4ca3c04f",
    "corpus_database_id": "repo_search_osf_187d493c5dae",
    "name": "Reproducibility Project in Special Education",
    "previous_codex_decision": "deterministic_repair_exhausted",
    "decision_basis": "osf_inventory:no_files_found:m2xpj:providers=1 | files=0",
    "landing_url": "https://osf.io/m2xpj/",
    "raw_url": "",
    "question": "Codex deterministic provider/direct repair did not find a public local result artifact. Research whether this lead has a reusable Figure 1 result-bearing artifact (dataset, workbook, source-family table, supplement, repository, PDF/HTML table, or file inventory), or classify it as individual_paper_only, context_only, duplicate, reject_not_figure1, or no_public_artifact_found."
  },
  {
    "followup_id": "result_artifact_followup_681a2ceb87317bb5",
    "corpus_database_id": "domain_search_osf_346003e74a16",
    "name": "Rollout Design Replication Project",
    "previous_codex_decision": "deterministic_repair_exhausted",
    "decision_basis": "osf_inventory:no_files_found:rkqab:failed:{\"errors\":[{\"detail\":\"Not found.\"}],\"meta\":{\"version\":\"2.0\"}} | files=0",
    "landing_url": "https://osf.io/rkqab/",
    "raw_url": "",
    "question": "Codex deterministic provider/direct repair did not find a public local result artifact. Research whether this lead has a reusable Figure 1 result-bearing artifact (dataset, workbook, source-family table, supplement, repository, PDF/HTML table, or file inventory), or classify it as individual_paper_only, context_only, duplicate, reject_not_figure1, or no_public_artifact_found."
  },
  {
    "followup_id": "result_artifact_followup_9b973dba997e2470",
    "corpus_database_id": "domain_search_osf_08793226b32b",
    "name": "Sample size and replication: A census using the Reproducibility Project Psychology",
    "previous_codex_decision": "deterministic_repair_exhausted",
    "decision_basis": "osf_inventory:no_files_found:dn3fk:failed:{\"errors\":[{\"detail\":\"Not found.\"}],\"meta\":{\"version\":\"2.0\"}} | files=0",
    "landing_url": "https://osf.io/dn3fk/",
    "raw_url": "",
    "question": "Codex deterministic provider/direct repair did not find a public local result artifact. Research whether this lead has a reusable Figure 1 result-bearing artifact (dataset, workbook, source-family table, supplement, repository, PDF/HTML table, or file inventory), or classify it as individual_paper_only, context_only, duplicate, reject_not_figure1, or no_public_artifact_found."
  },
  {
    "followup_id": "result_artifact_followup_b66c391cbd28b417",
    "corpus_database_id": "repo_search_osf_5efbb2b834cb",
    "name": "The Reproducibility Project",
    "previous_codex_decision": "deterministic_repair_exhausted",
    "decision_basis": "osf_inventory:no_files_found:g4ntj:providers=1 | files=0",
    "landing_url": "https://osf.io/g4ntj/",
    "raw_url": "",
    "question": "Codex deterministic provider/direct repair did not find a public local result artifact. Research whether this lead has a reusable Figure 1 result-bearing artifact (dataset, workbook, source-family table, supplement, repository, PDF/HTML table, or file inventory), or classify it as individual_paper_only, context_only, duplicate, reject_not_figure1, or no_public_artifact_found."
  },
  {
    "followup_id": "result_artifact_followup_1a958c09143a3833",
    "corpus_database_id": "repo_search_osf_7661e903bf58",
    "name": "WP1 XP2a - Book of N: White [replication - open question]",
    "previous_codex_decision": "deterministic_repair_exhausted",
    "decision_basis": "osf_inventory:no_files_found:2qm8f:failed:{\"errors\":[{\"detail\":\"Not found.\"}],\"meta\":{\"version\":\"2.0\"}} | files=0",
    "landing_url": "https://osf.io/2qm8f/",
    "raw_url": "",
    "question": "Codex deterministic provider/direct repair did not find a public local result artifact. Research whether this lead has a reusable Figure 1 result-bearing artifact (dataset, workbook, source-family table, supplement, repository, PDF/HTML table, or file inventory), or classify it as individual_paper_only, context_only, duplicate, reject_not_figure1, or no_public_artifact_found."
  },
  {
    "followup_id": "result_artifact_followup_e1b400aec5ecc3b2",
    "corpus_database_id": "repo_search_osf_25a030cb8e72",
    "name": "WP1 XP2a - Book of N: White [replication]",
    "previous_codex_decision": "deterministic_repair_exhausted",
    "decision_basis": "osf_inventory:no_files_found:xt458:failed:{\"errors\":[{\"detail\":\"Not found.\"}],\"meta\":{\"version\":\"2.0\"}} | files=0",
    "landing_url": "https://osf.io/xt458/",
    "raw_url": "",
    "question": "Codex deterministic provider/direct repair did not find a public local result artifact. Research whether this lead has a reusable Figure 1 result-bearing artifact (dataset, workbook, source-family table, supplement, repository, PDF/HTML table, or file inventory), or classify it as individual_paper_only, context_only, duplicate, reject_not_figure1, or no_public_artifact_found."
  },
  {
    "followup_id": "result_artifact_followup_a0edbc4d3a731ec0",
    "corpus_database_id": "lead_mullinix_2015",
    "name": "Mullinix Leeper Druckman Freese 2015",
    "previous_codex_decision": "deterministic_repair_exhausted",
    "decision_basis": "dataverse_inventory:failed:no_dataverse_persistent_id",
    "landing_url": "https://dataverse.harvard.edu/dataverse/psrm",
    "raw_url": "",
    "question": "Codex deterministic provider/direct repair did not find a public local result artifact. Research whether this lead has a reusable Figure 1 result-bearing artifact (dataset, workbook, source-family table, supplement, repository, PDF/HTML table, or file inventory), or classify it as individual_paper_only, context_only, duplicate, reject_not_figure1, or no_public_artifact_found."
  }
]
```
