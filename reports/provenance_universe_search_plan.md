# Provenance Universe Search Plan

- Generated: 2026-05-05T15:21:58.423944+00:00
- Spec: `PROVENANCE_PIPELINE_SINGLE_SOURCE_OF_TRUTH.yml`
- Spec root: `PROVENANCE_PIPELINE_SINGLE_SOURCE_OF_TRUTH`
- TSV: `data/derived/effect_inflation_dataset/provenance_search_plan.tsv`
- Search tracks: 34
- Present seed artifacts: 63
- Missing seed artifacts: 0
- Present target files: 25
- Target tracks with no files yet: 5

This report is the top of the pipeline: plot universe, search space, search query family, search lead, then later result target. It makes the old hand-built search surface explicit before locating, obtaining, or verification strategies run.

## Summary

| Universe | Search Tracks |
| --- | --- |
| plot1_replication_pairs | 28 |
| plot2_published_paper_d_vs_n | 2 |
| plot3_preregistered_results | 2 |
| plot4_all_source_dn_dump | 2 |

| Lead Status | Search Tracks |
| --- | --- |
| not_started | 4 |
| seeded_from_existing_artifact | 5 |
| target_manifest_present | 25 |

## plot1_replication_pairs

Goal: Find additional corpus, database, repository, registry-database, source table, and replication-project sources that may contain larger-N replication/follow-up pairs for Figure 1.

Promotion gate: This plan does not promote directly to result targets. It promotes discovered leads only into CORPORA_AND_DATABASES.tsv. A later parser or manual triage step promotes a corpus/database row into source, source_access, source_file, source_source_mapping, source_result, and canonical_result rows only after it exposes pair-level fields or a plausible route to reconstruct them.

Minimum lead fields: corpus_database_id | name | record_kind | inventory_status | source_family | description | why_relevant | plot_universe_ids | current_scope_roles | figure1_replication_relevance | discovery_source | discovery_source_path | landing_url | raw_url | local_raw_paths | backing_files | expected_rows | known_pair_rows | result_fields_available | has_d_or_convertible_effect | has_n | has_replication_pair_mapping | blocker_codes | next_action

| Rank | Track | Status | Lead Type | Direction | Tools | Target | Present Seeds | Missing Seeds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | plot1_corpusdb_local_inventory_refresh | seeded_from_existing_artifact | corpus_or_database | corpus_database_first_then_parse_pairs | local_derived_inventory \| local_raw_inventory \| rg_local_repo |  | 7 | 0 |
| 2 | plot1_corpusdb_osf_dataverse_openicpsr_search | target_manifest_present | repository_package | corpus_database_first_then_parse_pairs | osf_api \| dataverse_api \| datacite_api \| github_code_search_or_clone | present_files(3) | 0 | 0 |
| 3 | plot1_corpusdb_bibliographic_corpus_paper_search | target_manifest_present | corpus_or_database | corpus_database_first_then_parse_pairs | crossref_api \| openalex_api \| pubmed_europepmc | present_files(2) | 0 | 0 |
| 4 | plot1_corpusdb_citation_snowball_from_known_sources | target_manifest_present | corpus_or_database | corpus_database_first_then_parse_pairs | crossref_api \| openalex_api \| manual_literature_review | present_files(1) | 2 | 0 |
| 5 | plot1_corpusdb_domain_specific_meta_research_search | target_manifest_present | corpus_or_database | corpus_database_first_then_parse_pairs | crossref_api \| openalex_api \| pubmed_europepmc \| osf_api \| dataverse_api | present_files(2) | 0 | 0 |
| 6 | plot1_corpusdb_code_and_file_name_search | target_manifest_present | candidate_result_table | corpus_database_first_then_parse_pairs | github_code_search_or_clone \| local_raw_inventory \| rg_local_repo | present_files(2) | 2 | 0 |
| 7 | plot1_corpusdb_registry_and_pilot_fullscale_search | target_manifest_present | registry_record | corpus_database_first_then_parse_pairs | clinicaltrials_api_v2 \| pubmed_europepmc \| crossref_api \| openalex_api | present_files(1) | 0 | 0 |
| 8 | plot1_corpusdb_dead_link_and_archive_recovery | target_manifest_present | repository_package | corpus_database_first_then_parse_pairs | wayback_cdx \| manual_literature_review \| local_raw_inventory | present_files(1) | 2 | 0 |
| 9 | plot1_corpusdb_manual_expert_suggestion_capture | target_manifest_present | manual_source_suggestion | corpus_database_first_then_parse_pairs | manual_literature_review | present_files(1) | 1 | 0 |
| 10 | plot1_corpusdb_repository_expanded_search | target_manifest_present | repository_package | corpus_database_first_then_parse_pairs | osf_api \| dataverse_api \| openicpsr_api_or_browser | present_files(1) | 0 | 0 |
| 11 | plot1_corpusdb_bibliographic_expanded_search | target_manifest_present | corpus_or_database | corpus_database_first_then_parse_pairs | openalex_api \| crossref_api \| pubmed_europepmc | present_files(1) | 0 | 0 |
| 12 | plot1_corpusdb_citation_expanded_search | target_manifest_present | corpus_or_database | corpus_database_first_then_parse_pairs | openalex_api \| crossref_api \| manual_literature_review | present_files(1) | 0 | 0 |
| 13 | plot1_corpusdb_domain_expanded_search | target_manifest_present | corpus_or_database | corpus_database_first_then_parse_pairs | openalex_api \| crossref_api \| pubmed_europepmc \| osf_api \| dataverse_api | present_files(1) | 0 | 0 |
| 14 | plot1_corpusdb_code_expanded_search | target_manifest_present | candidate_result_table | corpus_database_first_then_parse_pairs | local_raw_inventory \| rg_local_repo | present_files(1) | 0 | 0 |
| 15 | plot1_corpusdb_repository_provider_expanded_search | target_manifest_present | repository_package | corpus_database_first_then_parse_pairs | zenodo_api \| figshare_api \| dryad_api | present_files(1) | 0 | 0 |
| 16 | plot1_corpusdb_known_source_family_alias_expansion | target_manifest_present | corpus_or_database | corpus_database_first_then_parse_pairs | osf_api \| dataverse_api \| datacite_api \| zenodo_api \| figshare_api \| dryad_api \| openalex_api \| crossref_api | present_files(1) | 0 | 0 |
| 17 | plot1_corpusdb_alternate_vocabulary_expanded_search | target_manifest_present | corpus_or_database | corpus_database_first_then_parse_pairs | openalex_api \| crossref_api \| pubmed_europepmc \| osf_api \| dataverse_api \| datacite_api | present_files(1) | 0 | 0 |
| 18 | plot1_corpusdb_publication_data_link_graph_search | target_manifest_present | repository_package | corpus_database_first_then_parse_pairs | openaire_scholexplorer_api \| semantic_scholar_api \| datacite_api \| openalex_api \| crossref_api | present_files(1) | 0 | 0 |
| 19 | plot1_corpusdb_repository_directory_surface_search | target_manifest_present | repository_package | corpus_database_first_then_parse_pairs | repository_registry_search | present_files(1) | 0 | 0 |
| 20 | plot1_corpusdb_gpt_coverage_source_family_search | target_manifest_present | corpus_or_database | corpus_database_first_then_parse_pairs | openalex_api \| crossref_api \| pubmed_europepmc \| osf_api \| dataverse_api \| datacite_api \| zenodo_api \| figshare_api \| dryad_api | present_files(1) | 0 | 0 |
| 21 | plot1_corpusdb_special_source_surface_search | target_manifest_present | repository_package | corpus_database_first_then_parse_pairs | manual_literature_review \| repository_registry_search | present_files(1) | 0 | 0 |

### plot1_corpusdb_local_inventory_refresh

Seed queries: replication source catalog | replication lead registry | corpus suggestion tracker | raw corpus candidates with replication files | staged or promoted replication harvest outputs | source catalogs mentioning replication, follow-up, reproduction, robustness, pilot, or full-scale

Accept if: source appears to contain multiple studies, papers, claims, trials, replication attempts, or pair rows | source may expose original/replication relationship fields, D/N fields, or conversion inputs | source has a local path, URL, citation, package, article, or other retrievable lead artifact

Reject if: individual replication paper only; route to individual replication-paper search instead | narrative review with no dataset, appendix, code, workbook, or row-level table | duplicate of existing CORPORA_AND_DATABASES.tsv row unless it adds a new artifact or route

Stop conditions: every local candidate has a row in CORPORA_AND_DATABASES.tsv with status, source path, and next action | duplicate source families have a single preferred corpus_database_id and alias notes

Seed artifacts: present_file:data/derived/effect_inflation_dataset/plot1_replication_source_catalog.csv | present_file:data/raw/replication_projects/lead_registry.csv | present_file:data/derived/replication_pairs/replication_source_worklist.csv | present_dir(43):data/raw/corpus_candidates | present_dir(30):data/raw/replication_projects | present_file:reports/corpus_suggestion_tracker.md | present_file:reports/corpus_candidates/replication_lead_queue.md

Outputs: CORPORA_AND_DATABASES.tsv

### plot1_corpusdb_osf_dataverse_openicpsr_search

Seed queries: "direct replication" data original replication | "replication study" "original study" dataset | "replication project" effect size sample size | "registered replication report" data | "Many Labs" replication data | "Reproducibility Project" coded data | "pilot" "full-scale" trial effect size | "original" "replication" "Cohen" "N" | "replication" "original_N" "replication_N" | "replication" "effect_size" "sample_size"

Accept if: repository contains a table, workbook, code output, or package with multiple original/replication rows | file inventory suggests fields for original source, replication source, effect, N, p-value, standard error, or outcome | package has enough documentation to classify the replication relation

Reject if: package supports one individual paper only and has no multi-row corpus/database role | package has no row-level artifact and only stores manuscript PDFs or slides | package cannot be lawfully inventoried or mirrored enough to triage

Stop conditions: repository query manifests are saved or summarized | every accepted repository lead lands in CORPORA_AND_DATABASES.tsv with repository URL and next action | every rejected repository lead has blocker_codes and rejection basis

Seed artifacts: 

Target glob: `steps/searches/figure1/corporasearch-repository-*.*` (present_files(3); skip_if_exists_unless_replace)

Example target files: steps/searches/figure1/corporasearch-repository-osf-dataverse-replication-project-effect-size.json | steps/searches/figure1/corporasearch-repository-osf-direct-replication-data-original-replication.json | steps/searches/figure1/corporasearch-repository-dataverse-registered-replication-report-data.json | steps/searches/figure1/corporasearch-repository-openicpsr-reproducibility-project-coded-data.json

Outputs: CORPORA_AND_DATABASES.tsv

### plot1_corpusdb_bibliographic_corpus_paper_search

Seed queries: "replication database" psychology | "replication database" "effect size" | "database of replication studies" | "replication success" "original study" | "replication rates" "coded" "effect sizes" | "large-scale replication" "dataset" | "multi-site replication" "dataset" | "replication project" "sample size" "effect size" | "original and replication" "effect size" "sample size" | "reproducibility project" "effect sizes"

Accept if: article describes or releases a corpus/database of replications, not merely one replication | abstract, supplement, data availability statement, or references point to a dataset/package/table | paper is likely to expose both original and replication identifiers or coded paired outcomes

Reject if: article is a conceptual review with no accessible corpus/table lead | article reports only aggregate replication rates without row-level study data | article is an individual replication paper and should be routed to the individual-paper search

Stop conditions: bibliographic search strings and candidate decisions are recorded | accepted papers are entered in CORPORA_AND_DATABASES.tsv with DOI/URL and expected artifact route

Seed artifacts: 

Target glob: `steps/searches/figure1/corporasearch-bibliographic-*.*` (present_files(2); skip_if_exists_unless_replace)

Example target files: steps/searches/figure1/corporasearch-bibliographic-openalex-crossref-replication-database-effect-size.json | steps/searches/figure1/corporasearch-bibliographic-openalex-replication-database-effect-size.json | steps/searches/figure1/corporasearch-bibliographic-crossref-database-of-replication-studies.json

Outputs: CORPORA_AND_DATABASES.tsv

### plot1_corpusdb_citation_snowball_from_known_sources

Seed queries: sources cited by current replication-project corpora | sources citing FReD, SCORE, LOOPR, RPP, Many Labs, RP:CB, and registered replication reports | papers sharing references with known replication database papers | datasets linked from known replication corpus articles | "FORRT Replication Database" OR FReD | "DARPA SCORE" replication database claims | "LOOPR" replication project | "Reproducibility Project: Psychology" dataset replication | "Many Labs" replication project dataset | "Social Science Replication Project" dataset | "Experimental Economics Replication Project" dataset | "Reproducibility Project: Cancer Biology" effect level data | "registered replication report" "many labs"

Accept if: citing/cited paper points to another replication corpus, coded replication table, or source package | relation to original/replication pair discovery is explicit or strongly suggested by metadata | lead can be represented by DOI, stable URL, repository URL, or local artifact path

Reject if: citation only discusses replication without releasing or naming a source table | source is already represented with no new route, alias, or artifact

Stop conditions: each known high-yield corpus has citation-neighborhood search status | new leads and rejected near-duplicates are recorded in CORPORA_AND_DATABASES.tsv

Seed artifacts: present_file:CORPORA_AND_DATABASES.tsv | present_file:data/derived/effect_inflation_dataset/plot1_replication_source_catalog.csv

Target glob: `steps/searches/figure1/corporasearch-citation-snowball-*.*` (present_files(1); skip_if_exists_unless_replace)

Example target files: steps/searches/figure1/corporasearch-citation-snowball-known-replication-corpora.json | steps/searches/figure1/corporasearch-citation-snowball-fred-score-loopr-rpp.json

Outputs: CORPORA_AND_DATABASES.tsv

### plot1_corpusdb_domain_specific_meta_research_search

Seed queries: psychology replication database effect size | behavioral science replication dataset original study | management science replication project dataset | operations management replication project data | economics replication project original estimates | political science replication archive original replication | clinical trial pilot full-scale follow-up database | neuroscience replication dataset effect size sample size | education replication study database | preclinical replication project effect size

Accept if: source covers a field where Figure 1 pair rules could apply | source offers row-level data or code likely to reconstruct paired D/N or native-to-D inputs | source has enough metadata to decide whether replication/follow-up N is larger than original N

Reject if: source is only a meta-analysis of many original studies with no replication/follow-up relationship | source lacks sample-size fields and no source route can recover them

Stop conditions: each target field has at least one saved accepted or rejected search batch | field-specific blockers are summarized in CORPORA_AND_DATABASES.tsv notes

Seed artifacts: 

Target glob: `steps/searches/figure1/corporasearch-domain-*.*` (present_files(2); skip_if_exists_unless_replace)

Example target files: steps/searches/figure1/corporasearch-domain-multifield-replication-database-effect-size.json | steps/searches/figure1/corporasearch-domain-psychology-replication-database-effect-size.json | steps/searches/figure1/corporasearch-domain-clinical-pilot-fullscale-followup.json

Outputs: CORPORA_AND_DATABASES.tsv

### plot1_corpusdb_code_and_file_name_search

Seed queries: original_d replication_d | original_N replication_N | replication_pair | original_effect replication_effect | smaller_N larger_N | replication_success | effect_size sample_size original replication | direct_replication dataset | paired replication table

Accept if: file names, headers, code, or README text suggest row-level original/replication pairs | candidate artifact is a CSV, TSV, XLSX, RDS, SAV, DTA, JSON, package, or script output | parser or manual inspection can be assigned a next_action

Reject if: keyword match is only in prose with no table-like artifact | artifact is an already integrated promoted output with no new source-family value

Stop conditions: local and GitHub/file-name hits are deduped against CORPORA_AND_DATABASES.tsv | accepted hits record candidate artifact path or URL

Seed artifacts: present_dir(43):data/raw/corpus_candidates | present_dir(30):data/raw/replication_projects

Target glob: `steps/searches/figure1/corporasearch-code-*.*` (present_files(2); skip_if_exists_unless_replace)

Example target files: steps/searches/figure1/corporasearch-code-local-original-replication-fields.json | steps/searches/figure1/corporasearch-code-original-n-replication-n.tsv | steps/searches/figure1/corporasearch-code-original-d-replication-d.tsv

Outputs: CORPORA_AND_DATABASES.tsv

### plot1_corpusdb_registry_and_pilot_fullscale_search

Seed queries: pilot trial full-scale follow-up same intervention outcome | feasibility pilot definitive trial effect size sample size | trial replication original trial follow-up larger sample | registered trial replication study original trial | clinical trial reproducibility database

Accept if: registry/database source could produce many pilot/full-scale or original/follow-up pairs | source includes trial identifiers, outcomes, enrollment/analysis N, and publication links or result records | relation can be coded as follow-up, extension, or pilot/full-scale rather than ordinary unrelated trials

Reject if: single registry record only; route to individual-pair worklist if relevant | no systematic way to map original and follow-up trial records

Stop conditions: registry-derived corpus/database candidates are either entered, rejected, or deferred with blocker

Seed artifacts: 

Target glob: `steps/searches/figure1/corporasearch-registry-*.*` (present_files(1); skip_if_exists_unless_replace)

Example target files: steps/searches/figure1/corporasearch-registry-pilot-fullscale-followup.json

Outputs: CORPORA_AND_DATABASES.tsv

### plot1_corpusdb_dead_link_and_archive_recovery

Seed queries: dead links from known replication project papers | discontinued project pages naming replication data | old supplementary datasets referenced by replication corpus articles | archived OSF Dataverse GitHub OpenICPSR package URLs

Accept if: archived page or local mirror identifies a corpus/database or package likely to contain pair rows | archive route exposes metadata, file names, or bytes sufficient for triage

Reject if: archive has only a landing page and no dataset/source table indication | source cannot be identified beyond a dead URL with no title or provider

Stop conditions: every dead-link candidate has archive status and next_action

Seed artifacts: present_file:CORPORA_AND_DATABASES.tsv | present_dir(30):data/raw/replication_projects

Target glob: `steps/searches/figure1/corporasearch-archive-*.*` (present_files(1); skip_if_exists_unless_replace)

Example target files: steps/searches/figure1/corporasearch-archive-known-replication-project-urls.json | steps/searches/figure1/corporasearch-archive-known-replication-project-deadlinks.tsv

Outputs: CORPORA_AND_DATABASES.tsv

### plot1_corpusdb_manual_expert_suggestion_capture

Seed queries: user-suggested replication datasets | papers or corpora mentioned in notes but not yet inventoried | reviewer-suggested replication databases | source families seen in article introductions, appendices, or acknowledgments

Accept if: suggestion names a corpus/database/project/package or gives enough information to search it | relevance to original/replication or follow-up pair discovery is plausible

Reject if: suggestion is only a topic area with no named source or search route

Stop conditions: every manual suggestion is represented in CORPORA_AND_DATABASES.tsv with triage status

Seed artifacts: present_file:reports/corpus_suggestion_tracker.md

Target glob: `steps/searches/figure1/corporasearch-manual-*.*` (present_files(1); skip_if_exists_unless_replace)

Example target files: steps/searches/figure1/corporasearch-manual-expert-suggestion-tracker.json | steps/searches/figure1/corporasearch-manual-user-suggested-replication-datasets.tsv

Outputs: CORPORA_AND_DATABASES.tsv

### plot1_corpusdb_repository_expanded_search

Seed queries: "direct replication" "original study" "dataset" | "replication" "original" "sample size" "effect size" | "replication project" "coded data" "original study" | "paired replication" "effect size" "sample size" | "replication studies" "dataset" "effect size" "original" | "multi-lab replication" "dataset" "effect size" | "large-scale replication project" "original study" | "registered replication report" "dataset" "original study" | "replications and reversals" "database" | "replication package" "original" "replication" "sample size" | "original_effect" "replication_effect" | "original sample size" "replication sample size" | "original_n" "replication_n"

Accept if: repository metadata suggests multiple original/replication rows or a coded replication corpus | metadata names original and replication fields, effect-size fields, N fields, or pair identifiers | package appears to be a reusable database/corpus source rather than one paper's replication package

Reject if: repository supports one individual replication paper only | search hit is only a manuscript, slide deck, or methods discussion with no table/package route

Stop conditions: expanded repository manifest exists or is intentionally skipped because the target file already exists | marginal candidates are represented in the search-yield summary before root-table consolidation

Seed artifacts: 

Target glob: `steps/searches/figure1/corporasearch-repository-expanded-*.*` (present_files(1); skip_if_exists_unless_replace)

Example target files: steps/searches/figure1/corporasearch-repository-expanded-replication-corpus-database-package.json

Outputs: steps/searches/figure1/corporasearch-repository-expanded-replication-corpus-database-package.json | steps/searches/figure1/searchyield-figure1-corpusdb-summary.tsv

### plot1_corpusdb_bibliographic_expanded_search

Seed queries: "replication database" "original" "replication" | "replication database" "sample size" | "database of direct replications" | "systematic replication" "database" | "replication project" "coded data" | "replication project" "original study" "effect size" | "large-scale replication" "original study" | "multi-lab replication" "original study" | "registered replication report" "original study" | "direct replication" "effect sizes" "dataset" | "replication studies" "coded" "sample size" | "replications and reversals" "data" | "meta-scientific" "replication" "database" | "scientific claims" "replication" "database"

Accept if: article appears to describe, release, cite, or route to a multi-row replication corpus/database | abstract or metadata mentions original/replication coding, sample sizes, effect sizes, or a dataset | hit names another source family that should be searched or cataloged

Reject if: article is a single replication paper with no corpus/database role | article is only a conceptual/methods discussion and names no source table or package

Stop conditions: expanded bibliographic manifest exists or is intentionally skipped because the target file already exists | search-yield summary records marginal candidates and duplicate/noise volume

Seed artifacts: 

Target glob: `steps/searches/figure1/corporasearch-bibliographic-expanded-*.*` (present_files(1); skip_if_exists_unless_replace)

Example target files: steps/searches/figure1/corporasearch-bibliographic-expanded-replication-corpus-database.json

Outputs: steps/searches/figure1/corporasearch-bibliographic-expanded-replication-corpus-database.json | steps/searches/figure1/searchyield-figure1-corpusdb-summary.tsv

### plot1_corpusdb_citation_expanded_search

Seed queries: "FReD" "replication database" | "FORRT" "replication database" | "DARPA SCORE" "replication" "dataset" | "SCORE" "scientific claims" "replication" | "LOOPR" "replication" | "ReplicationWiki" "replication" | "ManyBabies" "replication data" | "ManyPrimates" "replication data" | "ManyClasses" "replication data" | "Many Labs" "original study" | "Social Science Replication Project" "effect size" | "Experimental Economics Replication Project" "effect size" | "Reproducibility Project: Cancer Biology" "effect size" | "Reproducibility Project: Psychology" "original study"

Accept if: named source or citation neighborhood exposes a corpus/database, dataset, or row-level package | lead is not already represented unless it adds an alias, URL, citation, or acquisition route

Reject if: citing/cited article only discusses replication generally | source is already represented and adds no new route

Stop conditions: expanded citation manifest exists or is intentionally skipped because the target file already exists | duplicated named-source hits are visible in the search-yield summary

Seed artifacts: 

Target glob: `steps/searches/figure1/corporasearch-citation-expanded-*.*` (present_files(1); skip_if_exists_unless_replace)

Example target files: steps/searches/figure1/corporasearch-citation-expanded-known-replication-databases.json

Outputs: steps/searches/figure1/corporasearch-citation-expanded-known-replication-databases.json | steps/searches/figure1/searchyield-figure1-corpusdb-summary.tsv

### plot1_corpusdb_domain_expanded_search

Seed queries: psychology direct replication database original study | social psychology replication project coded data | cognitive psychology replication dataset effect size | developmental psychology replication project data | language acquisition replication project data | education replication dataset original study effect size | special education replication database effect size | economics replication project data original study | experimental economics replication project data | political science replication data original study | management replication project original study effect size | marketing replication project data original study | operations management replication project data | preclinical cancer biology reproducibility project effect level data | clinical psychology replication project dataset sample size | medicine reproducibility project replication dataset effect size | neuroscience replication project data original study | ecology evolution replication project data effect size | software engineering replication package original replication | sports exercise replication project data sample size

Accept if: field-specific hit names a database, replication project, source table, or package that could contain multiple pair rows | source appears to expose effect/N fields or enough native values to compute D and N

Reject if: source is only a domain meta-analysis with no replication/follow-up relation | source is an individual replication paper and should move to the individual-paper worklist instead

Stop conditions: expanded domain manifest exists or is intentionally skipped because the target file already exists | marginal field-specific candidates are visible in the search-yield summary

Seed artifacts: 

Target glob: `steps/searches/figure1/corporasearch-domain-expanded-*.*` (present_files(1); skip_if_exists_unless_replace)

Example target files: steps/searches/figure1/corporasearch-domain-expanded-crossfield-replication-datasets.json

Outputs: steps/searches/figure1/corporasearch-domain-expanded-crossfield-replication-datasets.json | steps/searches/figure1/searchyield-figure1-corpusdb-summary.tsv

### plot1_corpusdb_code_expanded_search

Seed queries: original_sample_size replication_sample_size | original_n replication_n | orig_n repl_n | original_effect_size replication_effect_size | orig_effect repl_effect | replication_effect original_effect | original_study_id replication_study_id | original_paper replication_paper | claim_id replication_id effect_size | study_pair_id original replication | replication_database | replications_and_reversals

Accept if: local file name, header, or code path suggests original/replication pair rows | artifact is a table, workbook, package, script output, or code file that may point to one

Reject if: match only occurs in derived root-table projections or already integrated outputs with no new source value

Stop conditions: expanded code manifest exists or is intentionally skipped because the target file already exists | local duplicate/noise volume is visible in the search-yield summary

Seed artifacts: 

Target glob: `steps/searches/figure1/corporasearch-code-expanded-*.*` (present_files(1); skip_if_exists_unless_replace)

Example target files: steps/searches/figure1/corporasearch-code-expanded-local-pair-field-signatures.json

Outputs: steps/searches/figure1/corporasearch-code-expanded-local-pair-field-signatures.json | steps/searches/figure1/searchyield-figure1-corpusdb-summary.tsv

### plot1_corpusdb_repository_provider_expanded_search

Seed queries: "replication database" "original" "replication" | "replication dataset" "original study" | "replication project" "effect size" "sample size" | "direct replication" "original study" "data" | "registered replication report" "data" | "large-scale replication" "data" | "multi-lab replication" "data" | "reproducibility project" "effect size" | "original_effect" "replication_effect" | "original_n" "replication_n" | "original sample size" "replication sample size" | "study_pair_id" replication | "claim_id" replication "effect_size"

Accept if: provider metadata or file metadata suggests a reusable data/code package rather than a one-paper replication package | title, description, tags, or files suggest original/replication pair fields, effect fields, N fields, or source-family artifacts | package can be inventoried through public metadata before any manual download is attempted

Reject if: hit is biological, database-system, or software-replication noise | package supports only one individual paper and has no source-family or multi-row corpus role | metadata is too thin to distinguish context paper from source object

Stop conditions: provider-expanded manifest exists or is skipped by target-file existence | marginal candidates are represented in the search-yield summary and later alias clusters

Seed artifacts: 

Target glob: `steps/searches/figure1/corporasearch-repository-provider-expanded-*.*` (present_files(1); skip_if_exists_unless_replace)

Example target files: steps/searches/figure1/corporasearch-repository-provider-expanded-zenodo-figshare-dryad-replication-corpus-database-package.json

Outputs: steps/searches/figure1/corporasearch-repository-provider-expanded-zenodo-figshare-dryad-replication-corpus-database-package.json | steps/searches/figure1/searchyield-figure1-corpusdb-summary.tsv

### plot1_corpusdb_known_source_family_alias_expansion

Seed queries: "FReD" "Replication Database" | "FORRT" "Replication Database" | "Replication Database" "original findings" "replication findings" | "Reproducibility Project: Psychology" data | "Reproducibility Project: Cancer Biology" "effect level data" | "Many Labs" "replication data" | "Many Labs 2" replication data | "Many Labs 3" replication data | "Many Labs 4" replication data | "Many Labs 5" replication data | "Registered Replication Report" "supplementary data" | "RRR" "registered replication report" data | "Social Science Replication Project" data | "Experimental Economics Replication Project" data | "ReplicationWiki" replication database | "SCORE" "scientific claims" data | "DARPA SCORE" "replication" data | "LOOPR" replication data | "ManyBabies" "replication data" | "ManyPrimates" "replication data" | "ManyClasses" "replication data" | "Metaketa" replication data | "BITSS" replication archive | "EGAP" replication archive

Accept if: known source-family alias resolves to a repository package, data paper, source project page, or row-level artifact | hit adds a new provider URL, DOI, component, file route, or alias to an existing source family | source-family appears to contain original/replication, follow-up, registered-report, or claim-replication relationships

Reject if: alias hit is only a secondary commentary or citation mirror with no new route | source is already represented and adds no new identifier, file route, or artifact family

Stop conditions: each high-value known source-family alias has saved provider/bibliographic lookup status | new aliases flow to alias clustering before review so the same source family is not reviewed repeatedly

Seed artifacts: 

Target glob: `steps/searches/figure1/corporasearch-sourcefamily-expanded-*.*` (present_files(1); skip_if_exists_unless_replace)

Example target files: steps/searches/figure1/corporasearch-sourcefamily-expanded-known-replication-project-aliases.json

Outputs: steps/searches/figure1/corporasearch-sourcefamily-expanded-known-replication-project-aliases.json | steps/searches/figure1/alias-clusters-leads-artifacts-root-v001.json

### plot1_corpusdb_alternate_vocabulary_expanded_search

Seed queries: "reproduction dataset" "original study" | "reproduction package" "original" "effect size" | "reanalysis" "original study" "replication" | "robustness" "replication" "dataset" | "external validation" "original study" dataset | "validation study" "original" "sample size" | "claim verification" dataset "effect size" | "claim replication" dataset | "benchmark replication" dataset | "many-lab" dataset original | "many lab" dataset original | "multi-site" replication dataset original | "multi-site" validation original study | "follow-up study" "original study" "effect size" | "follow-up" "original effect" sample size | "definitive trial" "pilot trial" "effect size" | "pilot trial" "full-scale" "sample size" | "replication archive" "original study" | "reproducibility dataset" "original study"

Accept if: source uses reproduction, reanalysis, robustness, validation, follow-up, many-lab, multi-site, or claim-verification language but still exposes reusable paired-source evidence | metadata or repository fields suggest original/follow-up, original/validation, original/reanalysis, or original/replication mappings | source has a dataset, repository, workbook, code package, source table, or file inventory route

Reject if: vocabulary refers to biology/DNA replication, software/database replication, or ordinary robustness checks with no replication/follow-up source relation | hit is a one-paper replication package without multi-row source-family value

Stop conditions: alternate-vocabulary manifest exists or is skipped by target-file existence | new aliases flow to clustering and review rather than directly mutating CORPORA_AND_DATABASES.tsv

Seed artifacts: 

Target glob: `steps/searches/figure1/corporasearch-alternate-vocab-expanded-*.*` (present_files(1); skip_if_exists_unless_replace)

Example target files: steps/searches/figure1/corporasearch-alternate-vocab-expanded-reproduction-reanalysis-validation-followup.json

Outputs: steps/searches/figure1/corporasearch-alternate-vocab-expanded-reproduction-reanalysis-validation-followup.json | steps/searches/figure1/searchyield-figure1-corpusdb-summary.tsv

### plot1_corpusdb_publication_data_link_graph_search

Seed queries: known corpus/database article DOI to DataCite related identifiers | known corpus/database article DOI to ScholeXplorer publication-data links | known corpus/database article DOI to Semantic Scholar references and citations | known source-family paper title to linked dataset/software records

Accept if: link graph exposes a dataset, software repository, supplement, or code package related to a known corpus/database article | linked object may contain row-level original/replication mappings or artifact inventories

Reject if: linked object is only the article PDF, citation mirror, or metadata page | relationship type is too vague and no artifact route exists

Stop conditions: every DOI-bearing accepted corpus/database article has a saved link-graph lookup artifact or explicit not-available reason

Seed artifacts: 

Target glob: `steps/searches/figure1/corporasearch-linkgraph-*.*` (present_files(1); skip_if_exists_unless_replace)

Example target files: steps/searches/figure1/corporasearch-linkgraph-expanded-known-corpus-paper-dois-to-datasets.json

Outputs: steps/searches/figure1/corporasearch-linkgraph-expanded-known-corpus-paper-dois-to-datasets.json

### plot1_corpusdb_repository_directory_surface_search

Seed queries: replication | reproduction archive | replication archive | social science data archive | psychology data repository | economics replication archive | political science data archive | clinical trial data repository | open science framework

Accept if: directory record names a repository likely to host replication, reproduction, validation, or source-family data packages | repository scope suggests a field-specific adapter may find corpus/database leads unavailable through generic search

Reject if: repository directory hit is biological/software/database-replication noise | repository is a broad archive with no realistic scoped query route

Stop conditions: repository-directory surface manifest exists or is skipped by target-file existence | useful surfaces are reviewed before building any custom adapter

Seed artifacts: 

Target glob: `steps/searches/figure1/searchsurface-repository-directory-*.json` (present_files(1); skip_if_exists_unless_replace)

Example target files: steps/searches/figure1/searchsurface-repository-directory-re3data-replication-repositories.json

Outputs: steps/searches/figure1/searchsurface-repository-directory-re3data-replication-repositories.json

### plot1_corpusdb_gpt_coverage_source_family_search

Seed queries: FIGURE1_REPLICATION_SOURCE_FAMILY_SEEDS.yml source_families[*].queries | FIGURE1_REPLICATION_SOURCE_FAMILY_SEEDS.yml source_families[*].aliases

Accept if: GPT coverage seed names a missing or undersearched source family and public metadata exposes a repository, dataset, project, registry, data paper, code package, or source-family page | search hit adds an alias, provider URL, DOI, or candidate artifact route for a named source family | lead can be clustered against existing roots before any table mutation

Reject if: result only repeats a known source without new alias or route | result is an individual article-level replication package rather than the named source family | result is a biology/software/database false positive

Stop conditions: GPT coverage target manifest exists or is skipped by target-file existence | any new hits flow into yield summary and alias clusters

Seed artifacts: 

Target glob: `steps/searches/figure1/corporasearch-gptcoverage-expanded-*.json` (present_files(1); skip_if_exists_unless_replace)

Example target files: steps/searches/figure1/corporasearch-gptcoverage-expanded-missing-source-family-targets.json

Outputs: steps/searches/figure1/corporasearch-gptcoverage-expanded-missing-source-family-targets.json

### plot1_corpusdb_special_source_surface_search

Seed queries: OpenReview ML_Reproducibility_Challenge group prefix | FORRT large-scale replication projects hub | Institute for Replication homepage | ReproSci Fly Immunity workspace | REPEAT Initiative homepage | ReScience C contents | X-Phi Replicability Project page | Data Colada replication archive | ManyBabies homepage | ManyPrimates homepage | EGAP Metaketa page | Sports Science Replication Centre homepage

Accept if: special source-family page or challenge group is reachable and can seed artifact inventory | page identifies a project, challenge, gateway, consortium, or source-family surface that public repository APIs do not expose well

Reject if: page is unreachable or only marketing/context with no route to reports, files, datasets, or article lists | source-family page lacks any explicit replication/follow-up/reproduction role

Stop conditions: special-source manifest exists or is skipped by target-file existence | accepted surfaces flow into alias clustering and review before root-table mutation

Seed artifacts: 

Target glob: `steps/searches/figure1/corporasearch-specialsurfaces-expanded-*.json` (present_files(1); skip_if_exists_unless_replace)

Example target files: steps/searches/figure1/corporasearch-specialsurfaces-expanded-openreview-rescience-gpt-source-family-pages.json

Outputs: steps/searches/figure1/corporasearch-specialsurfaces-expanded-openreview-rescience-gpt-source-family-pages.json

## plot1_replication_pairs

Goal: Find replication/follow-up source families and projects, then resolve the original target and both D/N sides of each pair.

Promotion gate: Promote only when a replication/follow-up lead exposes both sides, or enough source objects to resolve both sides, plus a relationship basis connecting the replication/follow-up result to the original claim. Do not require the original or replication to be published.

Minimum lead fields: lead_id | lead_title | source_family | replication_or_followup_source_hint | original_source_hint | pair_relationship_basis | expected_result_count | result_fields_available | candidate_artifact_path_or_url | triage_status

| Rank | Track | Status | Lead Type | Direction | Tools | Target | Present Seeds | Missing Seeds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | plot1_local_replication_harvest_inventory | seeded_from_existing_artifact | replication_project | replication_first_then_resolve_original | local_derived_inventory \| local_raw_inventory \| rg_local_repo |  | 8 | 0 |
| 2 | plot1_public_replication_project_search | not_started | repository_package | replication_first_then_resolve_original | osf_api \| dataverse_api \| openicpsr_api_or_browser \| github_code_search_or_clone \| crossref_api \| openalex_api |  | 2 | 0 |
| 3 | plot1_individual_gpt_assisted_pair_search | target_manifest_present | individual_replication_paper | replication_first_then_resolve_original | manual_literature_review \| crossref_api \| openalex_api \| pubmed_europepmc \| osf_api \| dataverse_api \| github_code_search_or_clone | missing | 3 | 0 |
| 4 | plot1_individual_bibliographic_phrase_search | target_manifest_present | individual_replication_paper | replication_first_then_resolve_original | crossref_api \| openalex_api \| pubmed_europepmc \| paperclip_hosted_index | missing | 0 | 0 |
| 5 | plot1_individual_repository_package_search | target_manifest_present | repository_package | replication_first_then_resolve_original | osf_api \| dataverse_api \| zenodo_api \| figshare_api \| dryad_api \| github_code_search_or_clone | missing | 0 | 0 |
| 6 | plot1_individual_known_original_citation_forward_search | target_manifest_present | individual_replication_paper | replication_first_then_resolve_original | openalex_api \| semantic_scholar_api \| crossref_api \| manual_literature_review | missing | 3 | 0 |
| 7 | plot1_individual_clinical_pair_rescue_search | target_manifest_present | individual_replication_paper | replication_first_then_resolve_original | pubmed_europepmc \| paperclip_hosted_index \| clinicaltrials_api_v2 \| crossref_api \| openalex_api | missing | 0 | 0 |

### plot1_local_replication_harvest_inventory

Seed queries: replication lead queue | staged replication harvest | promoted replication pairs | replication source worklist | original target resolution only after replication lead found

Accept if: paired_original_and_replication_fields_present | relationship_mapping_basis_present | D_or_native_effect_and_N_available_or_extractable | replication_or_followup_lead_found_before_original_resolution

Reject if: aggregate_only_without_pair_rows | replication_label_without_original_target | no_result_level_fields

Stop conditions: every existing lead is promoted, rejected, or assigned parser/blocker status

Seed artifacts: present_file:reports/corpus_candidates/replication_lead_queue.md | present_file:reports/corpus_candidates/replication_pair_source_catalog.md | present_file:data/derived/effect_inflation_dataset/plot1_replication_source_catalog.csv | present_file:data/derived/replication_pairs/harvest/lead_queue_status.csv | present_dir(65):data/derived/replication_pairs/harvest/staged | present_dir(33):data/derived/replication_pairs/harvest/promoted | present_file:data/derived/replication_pairs/replication_source_worklist.csv | present_file:data/raw/replication_projects/lead_registry.csv

Outputs: data/derived/effect_inflation_dataset/provenance_search_plan.tsv | future data/derived/effect_inflation_dataset/search_leads/plot1_replication_pairs.tsv

### plot1_public_replication_project_search

Seed queries: direct replication dataset | registered replication report data | Many Labs replication data | reproducibility project replication package | pilot full-scale replication psychology | follow-up study original target mapping

Accept if: project_contains_original_and_replication_mapping | row_level_effect_or_conversion_inputs_available | replication_or_followup_lead_found_before_original_resolution

Reject if: discussion_or_review_without_row_data | aggregate_meta_result_only

Stop conditions: repository search queries have saved result manifests and triage decisions

Seed artifacts: present_dir(69):data/raw/replication_projects/lead_harvest | present_dir(9):data/raw/replication_projects/manual_papers

Outputs: future data/derived/effect_inflation_dataset/search_leads/plot1_public_replication_project_search.tsv

### plot1_individual_gpt_assisted_pair_search

Seed queries: reports/figure1_individual_replication_search_help_prompt_2026-05-05.md | "failed to replicate" "effect size" "sample size" | "direct replication" "Cohen" "original study" | "we replicated" "sample size" "effect size" | "high-powered replication" "original effect" | "replication of" "original study" "sample size" | "larger sample" "replication" "original" | "follow-up study" "original effect" "sample size" | "definitive trial" "pilot trial" "effect size"

Accept if: candidate is a specific original/replication or original/follow-up pair | replication/follow-up relation is explicit in title, abstract, methods, report text, registry, or source package | source-object URLs exist for both represented sources or for a package/table that names both | candidate records effect/N availability or the exact source objects needed to check it

Reject if: answer only names another corpus/database without a concrete pair | later paper is merely related, citing, or conceptually adjacent with no replication/follow-up assertion | one-arm outcome lacks comparator and no native-only route is justified | same-data robustness/reanalysis is not labeled as reproduction or native/coverage-only

Stop conditions: GPT/Gemini output is saved as JSON with candidate-level source-object URLs and route decisions | every high-confidence candidate has a mirror-first object list or a documented access blocker | candidate pairs are deduped against FIGURE1_REPLICATION_PAIRS.tsv and known source families before extraction

Seed artifacts: present_file:reports/figure1_individual_replication_search_help_prompt_2026-05-05.md | present_file:steps/individual_replication_papers/figure1/individual-paper-worklist-from-cluster-review.tsv | present_file:steps/corpus_results/figure1/corpus_closure/figure1-corpus-dataset-closure-actions.tsv

Target glob: `steps/searches/figure1/individualrepsearch-gpt-*.json` (missing; skip_if_exists_unless_replace)

Example target files: steps/searches/figure1/individualrepsearch-gpt-batch001.json

Outputs: steps/searches/figure1/individualrepsearch-gpt-batch001.json | steps/individual_replication_papers/figure1/individual-paper-worklist-from-search.tsv

### plot1_individual_bibliographic_phrase_search

Seed queries: "failed to replicate" "original study" | "could not replicate" "original" "sample" | "direct replication" "original" "participants" | "registered replication report" "original study" | "replication attempt" "effect size" "N" | "high-powered" "direct replication" | "conceptual replication" "original effect" | "external validation" "original study" "effect size" | "pilot" "full-scale" "same outcome" "effect size"

Accept if: bibliographic record is an individual replication/follow-up paper or report | abstract or linked full text names the original study, target paper, phenomenon, or trial | DOI/PMID/PMCID/open-location route can ground at least the replication/follow-up source

Reject if: record is a review, editorial, meta-analysis-only source, or corpus/database already covered | no original target can be identified from metadata or full text

Stop conditions: phrase-search manifests record accepted, rejected, and duplicate candidates | accepted candidates route to individual-paper source-object acquisition rather than corpus intake

Seed artifacts: 

Target glob: `steps/searches/figure1/individualrepsearch-bibliographic-*.json` (missing; skip_if_exists_unless_replace)

Example target files: steps/searches/figure1/individualrepsearch-bibliographic-failed-to-replicate-effect-size.json | steps/searches/figure1/individualrepsearch-bibliographic-registered-replication-report-individual.json

Outputs: steps/searches/figure1/individualrepsearch-bibliographic-failed-to-replicate-effect-size.json

### plot1_individual_repository_package_search

Seed queries: "direct replication" "original study" data | "failed replication" data "original" | "registered replication report" "data" | "replication package" "original study" "sample size" | "replication" "original_n" "replication_n" | "original effect" "replication effect" | "replication" "supplementary data" "original effect"

Accept if: package is one paper's replication/follow-up package with source objects, data, code, or tables | file inventory suggests original/replication mapping, effect/statistic fields, N fields, or conversion inputs | package can be mirrored or sampled enough to decide Figure 1A/B/native/coverage route

Reject if: package is a corpus/database already routed through CORPORA_AND_DATABASES.tsv | package contains only preregistration, manuscript PDF, or materials with no result or source-object route

Stop conditions: accepted one-paper packages are queued for source-object acquisition and parsing | rejected repository hits include blocker_codes and relationship evidence status

Seed artifacts: 

Target glob: `steps/searches/figure1/individualrepsearch-repository-*.json` (missing; skip_if_exists_unless_replace)

Example target files: steps/searches/figure1/individualrepsearch-repository-osf-dataverse-single-replication-packages.json | steps/searches/figure1/individualrepsearch-repository-github-original-replication-fields.json

Outputs: steps/searches/figure1/individualrepsearch-repository-osf-dataverse-single-replication-packages.json

### plot1_individual_known_original_citation_forward_search

Seed queries: cited-by search around famous original effects not already covered by current source families | citing papers whose title or abstract contains replicate, replication, reproduce, robustness, follow-up, validation, re-test, or high-powered | citing papers of original effects in staged-unpromoted individual leads | citation neighborhoods around request-only corpus rosters where individual public source objects may rescue rows

Accept if: citing/follow-on paper self-describes a replication, validation, follow-up, or reproduction of the original | original and follow-up source objects can be grounded by DOI/PMID/PMCID/URL | candidate looks outside already-covered corpus rows or records its likely overlap for dedupe

Reject if: citing paper merely discusses, cites, extends theory, or includes the original in a literature review | no result-level source-object route is visible

Stop conditions: known-original forward-search batches have explicit yield and duplicate/noise notes | accepted pairs are queued with both source identities and mirror-first URLs

Seed artifacts: present_file:FIGURE1_REPLICATION_PAIRS.tsv | present_file:steps/corpus_results/figure1/corpus_closure/figure1-corpus-dataset-closure-actions.tsv | present_file:steps/individual_replication_papers/figure1/individual-paper-worklist-from-cluster-review.tsv

Target glob: `steps/searches/figure1/individualrepsearch-citation-*.json` (missing; skip_if_exists_unless_replace)

Example target files: steps/searches/figure1/individualrepsearch-citation-known-originals-forward-replication.json

Outputs: steps/searches/figure1/individualrepsearch-citation-known-originals-forward-replication.json

### plot1_individual_clinical_pair_rescue_search

Seed queries: "pilot trial" "full-scale trial" "same outcome" | "feasibility trial" "definitive trial" "effect size" | "phase II" "phase III" "same endpoint" | "follow-up randomized trial" "pilot" | "replication" "randomized trial" "original trial" | "external validation" clinical trial original study effect

Accept if: paper pair has same or close-enough clinical endpoint and intervention/comparator relationship | original and follow-up Ns are available from trial reports, registry records, or full text | effect measure is direct D/SMD, comparative binary D-equivalent, HR/RR/OR with conversion policy, or native-only with explicit route

Reject if: one-arm ORR lacks a comparator | trial relationship is ordinary development sequence with no affirmative replication/follow-up linkage | result values are request-only and no public source object exists

Stop conditions: clinical individual-pair candidates are separated into strict, D-equivalent, native, coverage-only, and rejected ledgers

Seed artifacts: 

Target glob: `steps/searches/figure1/individualrepsearch-clinical-*.json` (missing; skip_if_exists_unless_replace)

Example target files: steps/searches/figure1/individualrepsearch-clinical-pilot-definitive-public-source-objects.json

Outputs: steps/searches/figure1/individualrepsearch-clinical-pilot-definitive-public-source-objects.json

## plot2_published_paper_d_vs_n

Goal: Find published-paper result corpora that expose D/N, native statistics, or conversion inputs with paper grouping and selector metadata.

Promotion gate: Promote only when rows can be tied to published papers and expose D/N, native statistics, or deterministic conversion inputs. Main-result selector strength must be explicit, not inferred from corpus name.

Minimum lead fields: lead_id | corpus_name | source_family | paper_unit_count | result_row_count | journal_provenance_status | paper_grouping_status | d_n_availability_status | main_selector_status | candidate_artifact_path_or_url | triage_status

| Rank | Track | Status | Lead Type | Direction | Tools | Target | Present Seeds | Missing Seeds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | plot2_local_candidate_corpus_inventory | seeded_from_existing_artifact | corpus_or_database |  | local_derived_inventory \| local_raw_inventory \| rg_local_repo |  | 8 | 0 |
| 2 | plot2_article_corpus_discovery | not_started | corpus_or_database |  | crossref_api \| openalex_api \| pubmed_europepmc \| osf_api \| dataverse_api \| github_code_search_or_clone |  | 2 | 0 |

### plot2_local_candidate_corpus_inventory

Seed queries: candidate D/N rows | published paper source catalog | peer reviewed main result status | corpus suggestion tracker

Accept if: paper_units_identified | D_N_or_conversion_inputs_available | source_family_and_selector_status_recorded

Reject if: row_level_tests_without_paper_grouping | nonpublished_or_registry_only_scope | no_D_N_or_conversion_inputs

Stop conditions: every catalog source has include/exclude/comparator status and reason

Seed artifacts: present_file:reports/corpus_suggestion_tracker.md | present_file:data/derived/effect_inflation_dataset/plot2_published_source_catalog.csv | present_file:data/derived/effect_inflation_dataset/plot2_published_criteria_matrix.csv | present_file:data/derived/effect_inflation_dataset/plot2_published_paper_details.csv | present_file:data/derived/corpus_candidates/candidate_d_n_rows.csv.gz | present_file:data/derived/corpus_candidates/candidate_d_n_papers.csv | present_file:data/derived/corpus_candidates/current_peer_reviewed_main_result_status.csv | present_file:data/raw/corpus_candidates/metabus/Ver2-08_MasterDB_JAP-PPsych_1980-2010.xlsx

Outputs: data/derived/effect_inflation_dataset/provenance_search_plan.tsv | future data/derived/effect_inflation_dataset/search_leads/plot2_published_paper_corpora.tsv

### plot2_article_corpus_discovery

Seed queries: effect size sample size dataset | published article effect size corpus | focal effect psychology corpus | main result coded article sample | meta-analysis source estimate dataset publication flag | test statistic corpus sample size

Accept if: corpus_has_paper_or_article_identifiers | result_rows_have_effect_and_N_or_inputs | extraction_rule_can_be_written

Reject if: metadata_only_corpus | no_public_or_mirrorable_row_level_artifact | effect_scale_cannot_be_related_to_D

Stop conditions: query manifests and candidate rejections are saved for each search surface

Seed artifacts: present_dir(43):data/raw/corpus_candidates | present_dir(10):reports/corpus_candidates

Outputs: future data/derived/effect_inflation_dataset/search_leads/plot2_article_corpus_discovery.tsv

## plot3_preregistered_results

Goal: Find preregistered, PAP, registry, or registered-report result sources with explicit selector evidence and D/N or conversion inputs.

Promotion gate: Promote only when preregistration/PAP/registered-report/registry selector evidence is explicit and the candidate exposes D/N, native outcome data, or deterministic conversion inputs.

Minimum lead fields: lead_id | registry_or_preregistration_name | registration_id_or_url | preregistration_timing_status | selector_evidence_type | result_field_status | represented_paper_or_trial_hint | candidate_artifact_path_or_url | triage_status

| Rank | Track | Status | Lead Type | Direction | Tools | Target | Present Seeds | Missing Seeds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | plot3_local_registry_and_pap_inventory | seeded_from_existing_artifact | preregistration_or_pap |  | local_derived_inventory \| local_raw_inventory \| rg_local_repo |  | 11 | 0 |
| 2 | plot3_public_registry_search | not_started | registry_record |  | clinicaltrials_api_v2 \| aea_rct_registry_csv \| osf_api \| dataverse_api \| openicpsr_api_or_browser \| github_code_search_or_clone \| paperclip_hosted_index |  | 3 | 0 |

### plot3_local_registry_and_pap_inventory

Seed queries: plot3 preregistered source catalog | AEA registry candidates | CTGov registered medians | political science strict rescue rows | Scheel quote-stat rescue

Accept if: explicit_prereg_or_registry_selector | result_value_and_N_or_inputs_available | represented_trial_or_paper_can_be_identified

Reject if: preregistration_status_only_without_result_fields | posthoc_or_unclear_timing | source_is_sidecar_comparator_only

Stop conditions: every preregistered source catalog item has include/exclude/comparator status

Seed artifacts: present_file:data/derived/effect_inflation_dataset/plot3_preregistered_source_catalog.csv | present_file:data/derived/effect_inflation_dataset/plot3_preregistered_results.tsv | present_file:data/derived/effect_inflation_dataset/plot3_preregistered_criteria_matrix.csv | present_file:data/derived/effect_inflation_dataset/plot3_aea_registry_governance_candidates.csv | present_file:data/derived/effect_inflation_dataset/plot3_ctgov_api_registered_summary.csv | present_file:data/derived/effect_inflation_dataset/plot3_ctgov_api_registered_trial_medians.csv | present_file:data/derived/effect_inflation_dataset/plot3_ctgov_phase2plus_primary_randomized_sidecar_rows.csv | present_file:data/derived/effect_inflation_dataset/plot3_political_science_strict_rescue_rows.csv | present_file:data/derived/effect_inflation_dataset/plot3_political_science_rescue_worklist.csv | present_file:data/derived/effect_inflation_dataset/plot3_scheel_quote_stat_rescue_candidates.csv | present_file:data/raw/publication_bias_direct/aea_rct_registry/current_site_csv.csv

Outputs: data/derived/effect_inflation_dataset/provenance_search_plan.tsv | future data/derived/effect_inflation_dataset/search_leads/plot3_preregistered_results.tsv

### plot3_public_registry_search

Seed queries: pre-analysis plan treatment effect sample size | registered report hypothesis effect size | AEA RCT registry results paper replication data | OSF registration primary outcome result | ClinicalTrials.gov primary outcome group data | EGAP PAP replication data

Accept if: selector_mapping_can_be_written | outcome_result_fields_available | source_or_package_can_be_mirrored

Reject if: registry_entry_without_results | preregistered_design_without_published_or_registry_outcome | duplicate_of_existing_plot3_source

Stop conditions: registry/repository result manifests and rejected reasons are saved

Seed artifacts: present_dir(42):data/raw/publication_bias_direct | present_dir(13):data/raw/corpus_candidates/political_science_unlock | present_file:reports/plot3_more_preregistered_results_search_prompt_2026-04-27.md

Outputs: future data/derived/effect_inflation_dataset/search_leads/plot3_public_registry_search.tsv

## plot4_all_source_dn_dump

Goal: Find all source-family D/N rows useful for diagnostics, comparators, exclusions, and inclusion auditing.

Promotion gate: Promote broadly when source-family, D/N or native effect/N fields, and diagnostic inclusion role are explicit. Plot-specific inclusion can stay negative while the source remains useful for the all-source dump.

Minimum lead fields: lead_id | source_family | universe_overlap | source_kind | row_count_hint | D_N_or_native_metric_status | inclusion_role | candidate_artifact_path_or_url | triage_status

| Rank | Track | Status | Lead Type | Direction | Tools | Target | Present Seeds | Missing Seeds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | plot4_all_local_source_family_inventory | seeded_from_existing_artifact | candidate_result_table |  | local_derived_inventory \| local_raw_inventory \| rg_local_repo |  | 6 | 0 |
| 2 | plot4_sidecar_and_comparator_search | not_started | manual_source_suggestion |  | local_raw_inventory \| local_derived_inventory \| manual_literature_review \| rg_local_repo |  | 3 | 0 |

### plot4_all_local_source_family_inventory

Seed queries: plot source family membership | all source dump catalog | all source D/N rows | plot paper membership

Accept if: source_family_recorded | D_N_or_native_metric_fields_present | inclusion_or_exclusion_role_recorded

Reject if: no_numeric_result_surface | source_family_cannot_be_identified

Stop conditions: every source family has row counts, plot overlap, and diagnostic role

Seed artifacts: present_file:data/derived/effect_inflation_dataset/plot_source_family_membership.tsv | present_file:data/derived/effect_inflation_dataset/plot4_all_source_dump_catalog.csv | present_file:data/derived/effect_inflation_dataset/plot4_all_source_dn_rows.csv | present_file:data/derived/effect_inflation_dataset/plot_dot_membership.tsv | present_file:data/derived/effect_inflation_dataset/plot_paper_membership.tsv | present_file:data/derived/effect_inflation_dataset/plot_paper_summary.tsv

Outputs: data/derived/effect_inflation_dataset/provenance_search_plan.tsv | future data/derived/effect_inflation_dataset/search_leads/plot4_all_source_families.tsv

### plot4_sidecar_and_comparator_search

Seed queries: comparator source not included | sidecar sensitivity rows | source family excluded | diagnostic D/N rows

Accept if: sidecar_source_has_D_N_surface | relationship_to_main_plot_universe_recorded

Reject if: narrative_only_source | duplicate_of_existing_source_family

Stop conditions: comparator and exclusion leads are explicit rather than buried in prose

Seed artifacts: present_file:reports/corpus_suggestion_tracker.md | present_file:reports/plot3_sidecar_comparability_decision_2026-04-27.md | present_file:data/derived/effect_inflation_dataset/plot_paper_exclusivity_audit.tsv

Outputs: future data/derived/effect_inflation_dataset/search_leads/plot4_sidecar_and_comparator_search.tsv

## Operating Notes

- This file does not run broad external scraping. It centralizes what should be searched and what a lead must contain.
- Search executors should write each track's target file first, then update the consolidated output table. If the target file already exists, skip the track unless an explicit replace flag is set.
- A future executor can consume `provenance_search_plan.tsv`, emit one target manifest per track, update the consolidated intake table, and then hand promoted leads to identity, locating, and acquisition strategies.
- Search failures and rejected leads should stay append-only. They prevent repeated ad hoc searches from looking like new work.
