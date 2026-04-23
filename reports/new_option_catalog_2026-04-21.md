# New Option Catalog

Date: 2026-04-21

This note records the local verification pass on the latest batch of suggested
publication-bias datasets. The standard here was strict: a lead only counts as
public if there is a real downloadable/exportable file or a verified public
repository file. Gated GESIS/portal downloads are marked separately.

## Bottom Line

- `GESIS PubBias` is the strongest new Bucket 3 lead. It is a real file-backed
  dataset with a DOI, named files, and distribution URLs, but the downloads are
  gated behind GESIS access.
- `Moniz-Druckman-Freese 2025` is a real public denominator dataset on Harvard
  Dataverse and is directly downloadable.
- `COMPare` is stronger than the initial pass suggested. Beyond the 72-row
  master trial sheet, 59 public assessment sheets are now local and parse into
  1,171 outcome-level rows across primary, secondary, and non-prespecified
  outcomes.
- `Twomey 2021`, `Aczel 2018`, `Farrar 2023`, and `Edelsbrunner & Thurn 2024`
  are all real public row-level article-audit datasets.
- `Aczel 2018` is now in the normalized D/N build as an explicitly labeled
  comparator. It does not change the main published-focal counts.

## Verified Public And Downloadable

| Candidate | Bucket | Local files | What is actually public | Current decision |
|---|---|---|---|---|
| Twomey et al. 2021 | 1 / partial 2 | `data/raw/corpus_candidates/twomey_2021/raw_coding.csv`, `df_all.csv`, `osf_root.json` | `df_all.csv` is a 300-row article-level table with one DOI per row, support coding, sample size `n`, p-value reporting-type/threshold fields, preregistration/open-data flags, and clinical-trial/RCT labels. `raw_coding.csv` has 900 coder-level rows over the same 300 articles. | Track as a strong public article-audit dataset. Do not add to D/N build now because the released table lacks numeric exact p/test statistics. |
| Aczel et al. 2018 | 1 / narrow partial 2 | `data/raw/corpus_candidates/aczel_2018/data.csv`, `non_significant_table.xlsx`, `analysis.Rmd` | 175 negative-statement/statistic rows from 137 papers with article IDs, statistic type, p values, some `t` values, some `N1`/`N2`, and interpretation-category labels. The strict t-test subset in the authors' own analysis rule yields 62 usable D/N rows across 30 paper units. | Added to the normalized build as a clearly labeled comparator, not as part of the main focal-result cloud. |
| Farrar et al. 2023 | 1 | `data/raw/corpus_candidates/farrar_2023/AnimalCogNHSTData.xlsx`, `osf_root.json` | 303 article rows after header cleanup with title/abstract/result no-effect coding, result p-value fields, agreement/decision columns, and inclusion notes. | Tracker-only Bucket 1 audit; no sample-size layer found. |
| Edelsbrunner & Thurn 2024 | 1 | `data/raw/corpus_candidates/edelsbrunner_thurn_2024/Codings_analytic_share.xlsx`, `readme_anonymous.txt`, `Reproducible_Syntax_share.Rmd` | 528 hypothesis rows in `ModelData` plus 50 overlap rows, with non-significance, misinterpretation, implication, and rater fields. | Tracker-only Bucket 1 audit; no N/effect layer. |
| Moniz-Druckman-Freese 2025 TESS | 3 | `data/raw/publication_bias_direct/moniz_tess_2025/dataverse_meta.json`, `TESS_applicants.tab`, `README.txt`, `dataset_bundle.zip` | 544 researcher-project rows with accepted/declined status, write-up, journal submission, publication, top-journal placement, and `sig_find_strict`, plus respondent covariates. | Strong public denominator/status dataset. Not D-ready because no study-level N or numeric effect/test fields. |

## Verified But Access-Gated

| Candidate | Bucket | Local evidence | Access result | Current decision |
|---|---|---|---|---|
| GESIS PubBias / coded submissions and publications | 3 | `data/raw/publication_bias_direct/gesis_pubbias/gesis_page.html`, `gesis_schemaorg.json` | DOI `10.7802/2942` resolves to a real dataset record. JSON-LD lists `PubBias_Analysis dataset.dta`, `PubBias_Raw dataset.xlsx`, codebook, coding scheme, Stata prep code, and log file. Verified `access.gesis.org` distribution URLs return HTTP 403 without login. | Treat as the strongest yes-login Bucket 3 lead. Do not count it as anonymous public infrastructure. |

## High-Value Corrections To The Incoming Lead List

1. `Twomey 2021` is not just a dead data/code link. The OSF repository is real,
   public, and file-backed.
2. `Farrar 2023` has a real public workbook. The OSF item `84puf` is the coding
   guide file, not a second raw dataset.
3. `Edelsbrunner & Thurn 2024` has a real public workbook and syntax file.
4. `Aczel 2018` is a real public OSF project with structured tables, not just a
   vague data statement.
5. `Moniz-Druckman-Freese 2025` is a real public Dataverse package, but it is a
   denominator/status dataset rather than a numeric D/N dataset.
6. `COMPare` is no longer just a public Google Sheet and a set of HTML pages in
   the local catalog. The assessment-sheet layer is now mined into a tidy local
   outcome table:
   `data/derived/corpus_candidates/compare_trials/compare_trials_outcome_rows.csv`.

## Corrections To Later External Memo

The later external memo had useful signal, but several claims were materially
wrong or overstated.

1. `Schäfer & Schwarz 2019`:
   the locally verified public OSF node is `t8uvc`, already downloaded and
   parsed. The memo's alternative OSF IDs were not needed for acquisition, and
   the claim that the public release is simply "900 focal rows ready to go" is
   too loose. The verified usable counts are 682 non-preregistered rows and 89
   preregistered rows after requiring the actual numeric fields.

2. `Twomey 2021`:
   the memo treated this as a hidden-file near-hit under a different journal
   DOI. That is stale or mismatched. The kinesiology audit we verified is the
   public OSF project `nwcx6`, with a cleaned 300-row article table already
   local.

3. `Farrar 2023`:
   `84puf` is not a second raw dataset. It is the coding-guide file. The actual
   data workbook is `AnimalCogNHSTData.xlsx`.

4. `Edelsbrunner & Thurn 2024`:
   this is not a Type A focal-result dataset in the sense required for D/N
   work. The public workbook contains non-significance, misinterpretation, and
   implication coding, not a clean `N + effect/test statistic` layer.

5. `Moniz-Druckman-Freese 2025`:
   the Dataverse release is real and useful, but it does not expose numeric
   effect sizes or study-level sample sizes for a true numeric Type B build.

6. `GESIS PubBias`:
   this is a GESIS archive dataset with DOI `10.7802/2942`, not a verified CRAN
   package workflow. The strongest verified route is the archive record plus
   gated file-sharing URLs.

7. `Fanelli 2010`:
   the memo inflated the article count. The verified article record states that
   the study analyzed 2,434 papers, not about 4,600. A public row-level file
   is still unverified.

8. `Motyl et al. 2017`:
   the row-level audit data are genuinely public, but the canonical verified
   route in this repo is the OSF node `he8mu` containing `ScienceStatus_C.csv`.
   The later external note's `47yrm` pointer resolves to a different public OSF
   project titled `Racial Stereotype About Mental Illness`, with child SPSS
   files for four studies. That may be a real open project, but it is not the
   acquisition path used for the Motyl audit corpus here and should not replace
   `he8mu` in the tracker.

## Four-Study Audit Triage

The later four-study memo is useful, but only after separating its accurate
claims from the overstated ones.

- `Schäfer & Schwarz 2019`: accepted with caveat.
  Yes, this is one of the cleanest public row-level focal-effect corpora. The
  verified acquisition route remains OSF node `t8uvc`, not the alternative node
  IDs floated in the external memo.
- `Motyl et al. 2017`: accepted with caveat.
  Yes, public row-level audit files exist, but the stable verified route here is
  `he8mu` plus `ScienceStatus_C.csv`. The external memo's `47yrm` claim points
  to a different OSF project and should be treated as unverified for this
  corpus.
- `COMPare`: upgraded from partial public infrastructure to mined local corpus.
  There is still no neat DOI-backed tidy dataset release, but the public Google
  Sheets assessment URLs were enough to recover 59 local assessment CSVs. Those
  now yield 1,171 outcome rows in the derived table, with 89 prespecified
  primary rows, 660 prespecified secondary rows, and 422 non-prespecified
  publication rows. Eight assessment sheets remain auth-gated: study IDs `13`,
  `48`, `56`, `63`, `64A`, `64B`, `68`, and `69`.
- `Fanelli 2010`: unchanged negative verdict.
  Still no evidence of a public row-level file despite repeated checks. The
  practical status remains: classic study, internal coding table likely existed,
  public reusable file not found.

## Build Decision

Only one source from this batch was added to
`scripts/build_candidate_d_vs_n.py` in this pass: `Aczel 2018`.

Reasoning:

- `Twomey 2021` has article-level `n`, but the released p-value fields are
  reporting-format metadata and relative thresholds rather than exact numeric
  values.
- `Farrar 2023` and `Edelsbrunner & Thurn 2024` are coding datasets without the
  sample-size/effect layer needed for D/N.
- `Moniz-Druckman-Freese 2025` and `GESIS PubBias` are denominator datasets for
  publication status and significance/support coding, not numeric effect-size
  corpora.
- `Aczel 2018` was the one borderline case. I used the authors' own strict
  analyzable subset rule from `analysis.Rmd`: one-sample, paired-samples, and
  independent-samples t-tests with nonmissing `t` and `N1`. That yields 62
  usable comparator rows across 30 paper units. It enters the build as
  `aczel_2018_negative_claim_ttests`, with `published_original_candidate = False`
  and `comparator_only = True`, so it does not inflate the main published-focal
  counts.

## Immediate Follow-Up Targets

1. Keep `GESIS PubBias` in the tracker as a yes-login denominator target.
2. Use `Moniz-Druckman-Freese 2025` as a real public Bucket 3 reference point
   when comparing against nonpublic denominator studies such as Ross, Lee, and
   Rising.
