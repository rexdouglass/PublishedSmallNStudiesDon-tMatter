# Promising Pair-Source Failures Handoff

Generated for a follow-up GPT pass. This file documents sources that looked promising for original-vs-replication pair construction, but did not produce usable Plot 1 rows under the current rules.

## Current inclusion target

For the current Figure 2 / Plot 1 axis, a usable row needs:

1. an original side and a follow-up/replication side,
2. a common D/Z-convertible effect measure on both sides,
3. N on both sides,
4. both N values at least 10,
5. replication/follow-up N larger than original N.

The failures below are not all "bad sources." Several are real, public, and probably useful in a native-metric lane. They failed because they did not expose a clean original-vs-replication D/N pair table, because the payload was access-blocked, or because the available data are not on the current shared D/Z axis.

## Fast classification

| Source | Expected pair count or reason chased | Local outcome | Failure type | Best next GPT question |
| --- | ---: | --- | --- | --- |
| ManyBabies 3 | 15 possible infant rule-learning lab/site pairs | OSF and user ZIP are document-only; public GitHub has materials/not final data. A final manuscript/preprint trail may exist, but no public result repository is confirmed locally. Separate hcmv7 Marcus close-replication files are real, but they are not MB3 and the corresponding Marcus Experiment 2 pair is already present through FReD. | Missing final machine-readable MB3 pair results; hcmv7 is duplicate coverage | Is there a current public final MB3 results repo, accepted Stage-2 supplement, or OSF component not named `kqu9v`? |
| PSA 004 JTB Turri | 57 possible region/condition rows | One strict Darrel/Squirrel row is now rescued from article tables; region rows still need final Stage-2 data/analysis extraction. | Partial rescue; region payload still missing | Find the final Stage-2 PSA004 data/results location, not the original/pretest OSF node. |
| Eyewitness ten-country memory | 10 country-level replication rows expected | Five country rows are now rescued from the accepted-manuscript Hedges-g forest plot; public OSF payload remains unresolved. | Paper-fallback rescue | Locate the actual numeric supplement only if we want all country rows, aggregate rows, or audit provenance beyond the paper figure. |
| Media priming replication | 1 media-priming pair expected | Dataverse identifies `media_priming.xls`, but it is restricted; Cambridge article/appendix recover replication N but not a clean effect yet. | Effect still blocked | Find an unrestricted mirror of `media_priming.xls` or enough open table stats for one D/N pair. |
| Angrist learning-curve | Original Botswana plus country replications looked pairable | User-supplied OpenICPSR package is local, but files reproduce implementation-monitoring outputs, not a D/N treatment-effect pair table | Real data, wrong metric/table for this plot | Are treatment-effect estimates/Ns available in another AEA/OpenICPSR output file or only in the paper? |
| Wood and Porter backfire | 52 issue-level correction/backfire tests | Full Dataverse bundle is local; OSF `pes2y` lead was wrong | Native survey/correction metrics, no current D conversion policy | Build a native-metric conversion/mapping to Nyhan/Reifler, or identify a precomputed effect table. |
| Mullinix et al. 2015 | 20 survey-experiment generalizability rows | Full Dataverse bundle is local | Native survey ATE/generalizability metrics, not current D/N axis | Decide whether TESS-vs-MTurk ATEs can be standardized into this plot or need a separate lane. |
| EGAP Metaketa I | 24 field-experiment site/meta rows | GitHub archive is local with raw data and meta-analysis files | Native ATE/field-experiment lane, not smaller-original/larger-replication D/N | Treat as coordinated field-experiment evidence or find explicit study-level standardized effects. |
| EGAP Metaketa III | 30 field-experiment site/meta rows | Parent and component OSF packages are local | Native ATE/ITT lane, not current D/N pair table | Extract site estimates only if a native field-experiment lane is allowed. |
| EGAP Metaketa IV | 36 community-policing site/meta rows | OSF `xqd3v` results tree and selected country files are local | Native ATE/ITT lane, not current D/N pair table | Use study/meta RDS outputs for a native lane; do not force into D/Z without policy. |
| ERN/Pe RRR OpenNeuro | Raw EEG and RRR analysis looked promising | OSF summary/analysis artifacts are local; raw OpenNeuro lead exists | Replication-side native ERP material; original side missing | Find paper-level original-vs-replication ERN/Pe effect table or define ERP conversion policy. |
| Self-control fMRI | 4 Hare-vs-Scholz fMRI panels expected | OSF materials and open paper mirrors are local; no machine-readable pair table | Raw/native fMRI; paper fallback only | Extract from Scholz/Hare tables manually or find a supplement with both panels as data. |
| Border 2019 candidate gene | 150 historical candidate-gene rows expected | Public article/PDF local; AJP supplement endpoint blocked here | Native genetic metrics plus historical originals not tabulated | Find accessible supplementary tables and a mapping from historical gene studies to replication beta/OR. |
| ManyClasses 2 | 30 classroom intervention rows expected | Classroom analysis data/scripts are local | Original-side anchor missing; education-score metric not shared D/Z | Find the McDaniel original anchor on the same score scale or define education-score conversion. |
| Musicianship EEG | 5 neuroscience rows expected | GitHub zip local with MATLAB/code and processed EEG summaries | Original side missing; native EEG metric | Find original-small-N anchor and standardized site summary, or keep out. |
| News discernment replication | Follow-up intervention data looked relevant | Germany/France workbooks and R scripts local | Not an original-vs-replication pair table | Only use if a specific original and repeated follow-up contrast can be identified. |
| Nieuwland 2018 DeLong | 9 psycholinguistics lab rows expected | Only landing probe local | Conversion policy/data retrieval missing | Find the multi-lab data supplement and original DeLong effect/N on compatible scale. |
| Strategy-situation fit | 3 rows expected | Only landing probe local | Conversion policy/data retrieval missing | Fetch OSF data and identify original-side effect/N. |
| Awesome one-sided leads | Several direct-replication candidates in awesome-replicability-data | Matching folders are under `host_data_oneside`; files are covariates or one-sided payloads | Original side missing / source not pair-buildable | Search the original papers manually; the GitHub repo alone is insufficient. |

## Detailed notes

### ManyBabies 3

Why it looked promising:

- Multi-lab direct replication of Marcus-style infant rule learning.
- External research suggested a final analysis repository and site-level results.
- Staged as `expected_rows = 15`.

What is local:

- Staged file: `data/derived/replication_pairs/harvest/staged/manybabies_3__stage.csv`
- Raw directory: `data/raw/replication_projects/lead_harvest/manybabies_3/`
- OSF manifest/file list: `osf_manifest.json`, `osf_file_list.csv`
- User-supplied archive cached as `osfstorage_archive_user_20260426.zip`
- Public GitHub archive cached as `github_mb3_rules/mb3-rules-master.zip`
- Local OSF files are PDFs: preregistration reports, lab manual, pilot analysis, stimulus/norming, power analysis, supplemental.

What failed:

- The user-supplied OSF archive had the same document-only payload as the API pull.
- `mb3-rules` has stimuli, pilot materials, syllable ratings, and analysis notebooks, but not final infant site-level data/results.
- The reported `mb3-analysis` repository returned 404 during our pass.
- No final machine-readable lab/site result table was found.
- New outside research points to a 2026 PsyArXiv/preprint trail with 839 infants across 30 laboratories, but no public machine-readable site-level result repository has been confirmed locally.
- Follow-up check: `https://osf.io/hcmv7/` is a real four-lab close replication of Marcus et al. (1999), not a ManyBabies 3 final-results repository. Local files `data/raw/replication_projects/lead_harvest/marcus_four_lab_replication_hcmv7/Analyses.Rmd` and `Analyses.html` report the replication-side Marcus-style one-way analysis (`N = 96`, `F(1,95) = 0.148`, `p = .702`, `ges = 0.000307`). The user-supplied Marcus PDF confirms the original paper's Experiment 2 anchor (`N = 16`, Table 1 consistent mean = 5.6, inconsistent mean = 7.35, `F(1,14) = 25.6`, `p < .005`). That same pair is already in the corpus as `fred_soscisubmission55_1216`, so hcmv7 should be treated as provenance confirmation/duplicate coverage rather than a new promoted row.

What GPT should test:

- Search for a renamed or newly public final repository after Stage-2 acceptance.
- Search OSF child components not under `kqu9v`.
- Search the accepted manuscript supplement for "site-level", "lab-level", "looking time", "rule learning", "ABA", "ABB", or "Marcus".

### PSA 004 JTB Turri

Why it looked promising:

- Psychological Science Accelerator / Accelerated CREP replication of Turri, Buckwalter, and Blouw justified-true-belief materials.
- External research suggested many regions and public data/code.
- Staged as `expected_rows = 57`.

What is local:

- Staged file: `data/derived/replication_pairs/harvest/staged/psa_004_turri__stage.csv`
- Raw directory: `data/raw/replication_projects/lead_harvest/psa_004_turri/`
- Checked public materials include:
  - `osf_erm92/004_codebook.xlsx`
  - `osf_n5b3w/Primary analysis.R`
  - `osf_n5b3w/PRETEST/*.csv`
  - `osf_n5b3w_full/...`
  - `osf_psjxd/turri_fake_data.csv`

What failed:

- `erm92` surfaced a codebook, but processed-data and analysis children listed zero public files in our local crawl.
- `n5b3w` is original/pretest support plus analysis code, not a final PSA004 replication result payload.
- The material on hand still does not expose a machine-readable region-level pair-results table.
- Partial rescue: `scripts/promote_psa004_turri_article_tables.py` promotes one strict Darrel/Squirrel row from Hall et al. (2024) article tables. It uses original OR = 2.00, original N = 98, replication Table 7 counts `1126 knows / 454 believes` in the Darrel knowledge condition and `923 knows / 615 believes` in the Darrel Gettier condition, giving replication OR = 1.653 and replication N = 3,118. The ORs are mapped with Chinn's log-OR-to-d approximation.
- New promoted file: `data/derived/replication_pairs/harvest/promoted/psa004_turri_article_table_rescue__promoted_pairs.csv`
- New source reconstruction: `data/raw/replication_projects/lead_harvest/psa_004_turri/psa004_turri_article_table_reconstruction.csv`

What GPT should test:

- Find the actual Stage-2 data archive or journal supplement for `10.1177/25152459241267902` to recover the remaining region-level rows.
- Verify whether processed data are hidden behind OSF components that require a view-only link or different GUID.
- If only PDF/article tables exist, extract region-level N and effect/test-statistic manually.

### Eyewitness memory distortion in ten countries

Why it looked promising:

- Ten-country replication of Garry, French, Kinzett, and Mori co-witness memory distortion.
- External leads suggested an alternate OSF node with numeric `.xls` data and R code.
- Staged as `expected_rows = 10`.

What is local:

- Staged file: `data/derived/replication_pairs/harvest/staged/eyewitness_ten_countries_2018__stage.csv`
- Raw directory: `data/raw/replication_projects/lead_harvest/eyewitness_ten_countries_2018/`
- Local files: `landing_probe.json`, `landing_preview.bin`, `osf_manifest.json`, `osf_file_list.csv`

What failed:

- The live OSF storage listing for `a35rx` exposed no downloadable payload in our crawl.
- The suggested `tv9pg` node was checked and is a different eyewitness cross-examination project.
- The suggested `qbejt` node returned 404 locally.
- No country-level data table or R code is on hand from OSF.
- Partial rescue: `scripts/promote_eyewitness_ten_country_paper_tables.py` promotes five country rows from the accepted-manuscript forest plot. The source reports original New Zealand N = 40 and Hedges' g = 1.46, then country-level analyzed N and Hedges' g. The five countries with replication N > 40 are Canada, Malaysia, Poland, Turkey, and the United Kingdom.
- New promoted file: `data/derived/replication_pairs/harvest/promoted/eyewitness_ten_country_paper_table_rescue__promoted_pairs.csv`
- New source reconstruction: `data/raw/replication_projects/lead_harvest/eyewitness_ten_countries_2018/eyewitness_ten_country_accepted_manuscript_figure3.csv`
- The aggregate row was not promoted to avoid nested/non-independent rows in the current plot.

What GPT should test:

- Re-check the paper data availability statement and any journal supplemental files.
- Search exact title plus "Data S1", "numeric data", "R code", "Garry French Kinzett Mori", and "ten countries".
- Verify whether the data live in a private/view-only OSF link different from the public landing page, but this is no longer blocking the five paper-fallback rows.

### Media priming direct replication

Why it looked promising:

- The Harvard Dataverse metadata explicitly identifies `media_priming.xls`.
- Only one pair was needed.
- Staged as `expected_rows = 1`.

What is local:

- Staged file: `data/derived/replication_pairs/harvest/staged/media_priming_2017__stage.csv`
- Raw directory: `data/raw/replication_projects/lead_harvest/media_priming_2017/`
- Dataverse file list: `dataverse_file_list.csv`
- Local blocked payloads: `media_priming.xls` under the lead directory and under `dataverse_dvn_ecgado/`
- Public fallback: Cambridge appendix DOCX in `cambridge/` and `cambridge_appendix/`

What failed:

- Dataverse says `media_priming.xls` is restricted.
- Direct API download returned a small blocked/error payload rather than real Excel data.
- The Cambridge DOCX is useful as a paper/supplement fallback but is not the row-ready spreadsheet.
- New outside research reports `n_treatment = 52` and `n_control = 52`, so replication N = 104 is likely recoverable. The effect estimate is still missing, so no row was promoted.

What GPT should test:

- Find an unrestricted mirror of `media_priming.xls`.
- If no mirror exists, inspect the Cambridge appendix and article for enough statistics to create exactly one D/N row.
- Do not assume the local `.xls` files are valid; verify with file type and content first.

### Angrist learning-curve replication corpus

Why it looked promising:

- OpenICPSR package was expected to contain Stata data/code for a learning-curve replication corpus.
- User supplied the OpenICPSR package, now organized as `data/raw/replication_projects/lead_harvest/angrist_learning_curve_2023/openicpsr_189561_v1.zip`, which let us inspect the package locally.

What is local:

- Staged file: `data/derived/replication_pairs/harvest/staged/angrist_learning_curve_2023__stage.csv`
- Raw directory: `data/raw/replication_projects/lead_harvest/angrist_learning_curve_2023/`
- Local files include:
  - `openicpsr_189561_v1/main.do`
  - `openicpsr_189561_v1/accurate_targeting_week.dta`
  - `openicpsr_189561_v1/accurate_targeting_country.dta`
  - `openicpsr_189561_v1/operation_taught_all.dta`
  - `openicpsr_189561_v1/README.pdf`
  - paper PDF mirror

What failed:

- The local package reproduces implementation-monitoring outputs: `accurate_targeting` and operation-taught progression.
- It did not expose an original-vs-replication treatment-effect D/N table.
- The education/implementation outcomes do not sit cleanly on the current shared D/Z axis.

What GPT should test:

- Inspect any `Output/Tables` files if present in the source ZIP, especially treatment-effect tables rather than monitoring tables.
- Search AEA Data and Code for a separate package or appendix with country-level learning-effect estimates.
- If only paper tables exist, decide whether the paper can be manually converted or should remain native metric.

### Wood and Porter elusive backfire effect

Why it looked promising:

- Dataverse bundle is public and complete.
- The study tested many correction/backfire issues and was expected to provide about 52 issue-level pairs.
- Staged as `expected_rows = 52`.

What is local:

- Staged file: `data/derived/replication_pairs/harvest/staged/wood_porter_2019__stage.csv`
- Raw directory: `data/raw/replication_projects/lead_harvest/wood_porter_2019/`
- Full Dataverse bundle: `dataverse_bundle/dataverse_files.zip`
- File list includes R scripts and `elusive-tab *.tab` files.

What failed:

- Access did not fail; the data are local.
- The issue is metric/topology: survey correction/backfire estimates are native political-communication metrics.
- We do not yet have a documented mapping from Nyhan/Reifler original backfire quantities to Wood/Porter issue-level effects on the shared D/Z axis.
- The suggested OSF `pes2y` mirror was checked and appears to be a different fake-news memory project, not this payload.

What GPT should test:

- Identify whether Wood/Porter contains a precomputed table comparing original Nyhan/Reifler WMD effect to the relevant Wood/Porter WMD wording arm.
- If using all 52 issue rows, propose a transparent conversion from response-scale effects or regression coefficients to D/Z.
- Decide whether this belongs in a separate native political-communication lane.

### Mullinix, Leeper, Druckman, and Freese 2015

Why it looked promising:

- The project compares survey-experiment effects across convenience, student/staff, MTurk, and TESS/GfK style samples.
- Dataverse bundle is public and downloaded.
- Staged as `expected_rows = 20`.

What is local:

- Staged file: `data/derived/replication_pairs/harvest/staged/mullinix_2015__stage.csv`
- Raw directory: `data/raw/replication_projects/lead_harvest/mullinix_2015/`
- Bundle: `dataverse_dvn_mujhgr/dataverse_files.zip`

What failed:

- Access did not fail; the data are local.
- The source is real but currently native survey-ATE/generalizability material, not a strict original-small-N vs replication-large-N D/N table.
- It needs a policy decision: either standardize the ATEs and include them, or keep them in a native-metric lane.

What GPT should test:

- Look for an analysis-results table with arm Ns, means, and SDs that would support standardized mean differences.
- Decide whether TESS/GfK vs MTurk contrasts count as "original vs replication" for this paper's concept, or as external-validity/generalizability rows.

### EGAP Metaketa I, III, and IV

Why they looked promising:

- Coordinated multi-site political-science field experiments.
- External audit leads suggested site-level estimates and public data/code.
- Staged expected rows:
  - Metaketa I: 24
  - Metaketa III: 30
  - Metaketa IV: 36

What is local:

- Metaketa I staged file: `data/derived/replication_pairs/harvest/staged/metaketa_i_2019__stage.csv`
- Metaketa I raw: `data/raw/replication_projects/lead_harvest/metaketa_i_2019/github_metaketa_i/metaketa-i-main.zip`
- Metaketa III staged file: `data/derived/replication_pairs/harvest/staged/metaketa_iii_2021__stage.csv`
- Metaketa III raw includes `osf_259yz/Replication.zip`, `osf_td2p3/*.zip`, `osf_wscxp/*.Rdata`
- Metaketa IV staged file: `data/derived/replication_pairs/harvest/staged/metaketa_iv_2021__stage.csv`
- Metaketa IV raw includes selected `osf_xqd3v` result outputs and country files.

What failed:

- Access largely succeeded.
- These are coordinated field-experiment/meta-analysis sources with native ATE/ITT outputs.
- They are not straightforward smaller-original/larger-replication D/N pair sources under the current Plot 1 rule.

What GPT should test:

- Extract them only if we explicitly open a native field-experiment lane.
- Otherwise, find whether any paper tables already report standardized effects plus site Ns in a way that can be defensibly mapped to D/Z.

### ERN/Pe RRR OpenNeuro

Why it looked promising:

- Registered Replication Report plus OpenNeuro raw EEG and OSF analysis artifacts.
- Could plausibly include site-level ERN/Pe reliability/effect summaries.

What is local:

- Staged file: `data/derived/replication_pairs/harvest/staged/ern_pe_rrr_openneuro__stage.csv`
- Raw directory: `data/raw/replication_projects/lead_harvest/ern_pe_rrr_openneuro/`
- OSF artifacts include:
  - `osf_8cbua_7ku9r/ReliabilityTable.csv`
  - `osf_8cbua_7ku9r/rrr_ern_alldata.RData`
  - `osf_8cbua_7ku9r/gavs_stim.csv`
  - `osf_8cbua_7ku9r/gavs_resp.csv`
  - `osf_8cbua_yszgv/statistical_analysis.docx`

What failed:

- The available material is replication-side native ERP/reliability data.
- Original-side effects are not paired in the local artifacts.
- ERP amplitudes/reliability statistics need a domain-specific conversion policy before entering a D/Z plot.

What GPT should test:

- Search the RRR paper/supplement for an original-vs-replication table with N and ERN/Pe effect statistics.
- Decide whether to convert ERP effect estimates to D/Z or keep this as native neuroscience.

### Self-control fMRI replication

Why it looked promising:

- Replication of Hare et al. dietary self-control fMRI paradigm.
- External research suggested open paper/supplement with side-by-side original and replication panels.
- Staged as `expected_rows = 4`.

What is local:

- Staged file: `data/derived/replication_pairs/harvest/staged/self_control_fmri_2022__stage.csv`
- Raw directory: `data/raw/replication_projects/lead_harvest/self_control_fmri_2022/`
- OSF files include scripts, stimuli, preregistration, pilot materials.
- Paper mirrors are local:
  - `HBM-43-4995.pdf`
  - `paper_mirrors/scholz_hbm_2022.pdf`
  - `paper_mirrors/scholz_hbm_2022_eur.pdf`

What failed:

- No machine-readable original-vs-replication result table was found.
- OpenNeuro provides raw fMRI, but that implies reanalysis rather than direct pair extraction.
- Current blocker is both missing pair table and native fMRI metric alignment.

What GPT should test:

- Extract original-vs-replication stats from the local paper/supplement manually.
- Search for a supplement table with Hare 2009 panels and Scholz 2022 panels in machine-readable form.

### Border 2019 candidate-gene replication

Why it looked promising:

- Large-scale replication/retest of historical candidate-gene claims.
- External research suggested supplementary tables with beta/SE/p/N and candidate-gene rosters.
- Staged as `expected_rows = 150`.

What is local:

- Staged file: `data/derived/replication_pairs/harvest/staged/border_2019__stage.csv`
- Raw directory: `data/raw/replication_projects/lead_harvest/border_2019/`
- Local article mirror: `raw__Border_AJP_2019.pdf`

What failed:

- AJP supplement endpoint returned 403 in this environment.
- The public PDF is useful background but not a pair table.
- Historical original candidate-gene effects are not tabulated as matched original-vs-replication rows in the local material.
- Genetic metrics are native beta/OR/GWAS-style quantities, not current D/Z rows without a specific conversion policy.

What GPT should test:

- Locate accessible supplementary tables outside the blocked AJP endpoint, possibly via PMC or publisher mirrors.
- Determine whether historical original effects can be harvested from the primary candidate-gene literature rather than Border alone.
- Propose a genetic-effect metric lane if direct D conversion is not defensible.

### ManyClasses 2

Why it looked promising:

- Multi-classroom education intervention with local classroom data and scripts.
- Staged as `expected_rows = 30`.

What is local:

- Staged file: `data/derived/replication_pairs/harvest/staged/manyclasses_2__stage.csv`
- Raw directory: `data/raw/replication_projects/lead_harvest/manyclasses_2/`
- Local files include `analysis/*.Rdata`, preprocessing scripts, performance/view-duration/event-count scripts, and code workbooks.

What failed:

- The local files support within-source classroom intervention analysis.
- The original McDaniel anchor is not present locally on the same scale.
- It is not an explicit original-vs-replication D/N pair table.

What GPT should test:

- Find the original McDaniel effect and N on a compatible education-score scale.
- Decide whether classroom section replications should be native education-effect rows rather than D/Z rows.

### Musicianship EEG multi-site replication

Why it looked promising:

- Multi-site neuroscience/EEG replication/generalization source.
- Staged as `expected_rows = 5`.

What is local:

- Staged file: `data/derived/replication_pairs/harvest/staged/musicianship_eeg_2025__stage.csv`
- Raw directory: `data/raw/replication_projects/lead_harvest/musicianship_eeg_2025/`
- GitHub archive: `raw__MusicianshipEEG-main.zip`

What failed:

- The local GitHub zip contains MATLAB analysis code and processed EEG summaries.
- No explicit smaller-original/larger-replication D/N pair table was exposed.
- Original-side anchor and conversion policy are missing.

What GPT should test:

- Search for a paper supplement or results CSV with site-level effects and original N.
- Decide whether EEG summary metrics can be mapped to D/Z.

### News discernment replication

Why it looked promising:

- Real OSF payload with Germany/France clean data and analysis scripts.
- It looked like a misinformation/news replication/generalization source.

What is local:

- Staged file: `data/derived/replication_pairs/harvest/staged/news_discernment_replication__stage.csv`
- Raw directory: `data/raw/replication_projects/lead_harvest/news_discernment_replication/`
- Local files include:
  - `Germany_Clean.xlsx`
  - `France_Clean.xlsx`
  - `Script_main.R`
  - `Script_control.R`
  - `Script_placebo.R`
  - field materials DOCX/QSF files

What failed:

- The data are an intervention dataset, not an original-vs-replication pair table.
- No smaller-original/larger-replication anchor is identified locally.

What GPT should test:

- Identify whether this is a replication of a named original paper or simply a new cross-national study.
- If it is a replication, find the original and target contrast.

### Nieuwland 2018 DeLong replication

Why it looked promising:

- Multi-lab psycholinguistic replication of a DeLong sentence-comprehension effect.
- Staged as `expected_rows = 9`.

What is local:

- Staged file: `data/derived/replication_pairs/harvest/staged/nieuwland_2018_delong__stage.csv`
- Raw directory has only landing probe artifacts.

What failed:

- We did not retrieve the actual data/supplement.
- Current blocker is effect conversion policy and missing payload.

What GPT should test:

- Fetch the eLife article data/supplement and find lab-level N and effect/test statistics.
- Identify the original DeLong effect and N on the same comprehension/ERP scale.

### Strategy-situation fit replication

Why it looked promising:

- Recent direct replication with public-data lead.
- Staged as `expected_rows = 3`.

What is local:

- Staged file: `data/derived/replication_pairs/harvest/staged/strategy_fit_2025__stage.csv`
- Raw directory has only landing probe artifacts.

What failed:

- No result payload was downloaded locally.
- Conversion policy is missing.

What GPT should test:

- Revisit OSF `ap2ws` and look for child components/files that the crawl missed.
- Identify the exact original target and replication effect/N.

### Awesome-replicability one-sided leads

Why they looked promising:

- `awesome-replicability-data` yielded several excellent promoted pairs elsewhere.
- Several additional folders looked like direct replications.

What is local/staged:

- Staged files include:
  - `awesome_body_dissatisfaction__stage.csv`
  - `awesome_climate_misinfo__stage.csv`
  - `awesome_pain_tolerance__stage.csv`
  - `awesome_priming_exercise__stage.csv`
- These point to `host_data_oneside` paths in the GitHub repository.

What failed:

- The available original files are covariate summaries or one-sided materials, not original effect/N rows.
- Replication files may be raw session data, but without the original side they are not pair-buildable.

What GPT should test:

- For each one-sided lead, search the original paper directly for the target effect and N.
- If original-side values can be manually reconstructed, these may become usable despite the repo being one-sided.

## Lower-priority or support-only promising leads

These were real enough to log but are less likely to pay off quickly:

- `IBL reproducible electrophysiology`: landing probe only; native neuroscience source, not pair-buildable without domain extraction.
- `Jaljuli/Kafkafi multi-lab rodent replication`: landing probe only; conversion policy missing for rodent/preclinical metrics.
- `IES systematic replication awards` and `EEF regrants`: grant/project catalogs, not row-ready pair datasets.
- `Tyner/Nosek SCORE`: local OSF payload is sidecar/template material and overlaps existing SCORE analyst join.
- `Rescue17 / 28 classics`: local files are prediction-market/trading artifacts and supplements; live parsed pair table already represents the useful material elsewhere.

## Sources not to re-open as failures

- Coppock 2019 is not a failure. It has `data/derived/replication_pairs/harvest/promoted/coppock_generalizability__promoted_pairs.csv` with 50 promoted rows, 35 of which pass the current figure gates.
- Public-admin blame is not a failure. The paper tables were reconstructed into 9 promoted rows.
- RRR Colling SNARC is not a failure. Four Att-SNARC rows were promoted from the local GitHub archive.
- PSA 004 is now a partial rescue. One strict Darrel/Squirrel article-table row was promoted; the 57 expected region rows remain unresolved.
- Eyewitness ten-country is now a partial rescue. Five accepted-manuscript Hedges-g country rows were promoted; the OSF data payload remains unresolved.
- Marcus et al. infant rule learning / hcmv7 is not an additional ManyBabies 3 rescue. The hcmv7 analysis is real and the original Marcus PDF is local, but the matching original-vs-replication row is already present through FReD (`fred_soscisubmission55_1216`).
- Ying 2023 is only a partial failure. Two rows were promoted; five more are staged because exact pilot denominators, compatible SDs, or native HR-to-D policy are unresolved.

## Highest-yield next attempts

1. PSA 004: one row is rescued; the remaining payoff is the final processed-data OSF component or region-level journal supplement.
2. ManyBabies 3: high value, but only if final Stage-2 data have become public under a new repo/component.
3. Media priming: N appears recoverable, but the effect still needs Dataverse access, a mirror, or open appendix table extraction.
4. Eyewitness ten-country: five rows are rescued; continue only to find the actual data node or recover the remaining non-passing/support rows.
5. Self-control fMRI: paper fallback is local; a manual extraction pass may produce rows without new data.
6. Wood/Porter and Mullinix: do not need retrieval as much as a native-metric or D-conversion policy.
