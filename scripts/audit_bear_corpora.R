#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(dplyr)
  library(readr)
})

bear_path <- "data/raw/bear/BEAR.rds"
d_path <- "data/derived/bear/bear_d_values.csv.gz"
out_dir <- "data/derived/bear"
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

bear <- readRDS(bear_path)
d_values <- read_csv(d_path, show_col_types = FALSE)

row_counts <- bear %>%
  count(dataset, name = "bear_rows")

d_counts <- d_values %>%
  count(dataset, D_best_source, name = "d_rows_by_source") %>%
  group_by(dataset) %>%
  summarise(
    d_rows = sum(d_rows_by_source),
    d_sources = paste(paste0(D_best_source, "=", d_rows_by_source), collapse = "; "),
    .groups = "drop"
  )

d_summary <- d_values %>%
  group_by(dataset) %>%
  summarise(
    median_D = median(D_abs_best, na.rm = TRUE),
    p90_D = quantile(D_abs_best, 0.90, na.rm = TRUE, names = FALSE),
    median_ss = median(ss, na.rm = TRUE),
    .groups = "drop"
  )

manual <- tribble(
  ~dataset, ~domain, ~d_verdict, ~published_paper_isolation, ~treatment_interest_isolation, ~best_filter_in_bear, ~published_treatment_d_grade, ~notes,
  "ArelBundock", "political science", "yes", "partial_by_source_design", "no", "none; has field and metaid, but no publication-status or focal-treatment flag", "weak_for_target", "D uses z/N proxy from reported n. Corpus is estimates from published meta-analytic articles in political science, not a strict published-paper main-effect corpus.",
  "Askarov", "economics", "no_in_bear", "partial_by_source_design", "no", "none in BEAR; original data may have journal/meta-analysis fields", "not_usable_without_raw_inputs", "BEAR has coefficients and SEs but no sample size, so no D/N conversion here.",
  "BarnettWren", "biomedicine", "yes", "yes_by_source_design", "no", "source distinguishes MEDLINE vs PMC full text, not treatment/main outcome", "weak_for_target", "Published biomedical CIs from abstracts/full texts; D is log-ratio approximation. No sample size and no main-treatment flag.",
  "Bartos", "exercise", "yes", "partial_by_source_design", "partial", "subset=exercise/cognition category; no publication-status flag", "usable_with_caveats", "Effect-size estimates from meta-analyses of RCT exercise interventions. Treatment domain is coherent, but BEAR does not flag journal-published primary reports or one focal endpoint.",
  "Brodeur", "economics", "no_in_bear", "yes_by_source_design", "no", "method=RCT/IV/DID, year; no ss and no paper-main-effect flag", "not_usable_without_raw_inputs", "Published leading-economics articles, but BEAR lacks sample size and includes table-level test stats, not just treatment of interest.",
  "Chavalarias", "biomedicine", "no", "yes_by_source_design", "no", "source=MEDLINE/PMC full text; p-values only", "not_usable", "Published biomedical p-values, but no effect size or sample size for D and no treatment/main-outcome flag.",
  "clinicaltrials", "clinical trials", "yes", "no_registry_results", "yes_primary_outcomes", "dataset already keeps randomized interventional trials and primary outcomes; subset=phase; measure", "not_published_papers_but_good_toi", "Registry results, not journal publications. Good for primary treatment/outcome registry evidence, not published-paper filter.",
  "Cochrane", "medicine & health", "yes", "partial_source_data_type", "partial_first_comparison_outcome", "group=published/mixed/sought/unpublished; measure=SMD/probit; method=RCT/unknown", "best_available_in_bear", "Best BEAR corpus for this exact provenance question: source-data type plus first comparison/outcome. Still study-level source data, not strict one-journal-paper rows.",
  "CostelloFox", "ecology & evolution", "yes", "partial_by_source_design", "no", "measure; metaid; no publication-status or focal-treatment flag", "weak_for_target", "Meta-analytic ecology/evolution effects. D from native effect sizes/Fisher z. Not a treatment-of-interest paper corpus.",
  "euctr", "clinical trials", "yes", "no_registry_results", "yes_primary_endpoints", "dataset already keeps EU CTR result records/endpoints; measure", "not_published_papers_but_good_toi", "Registry results, not published papers. Good for primary endpoint evidence, not publication filter.",
  "Head", "biomedicine", "no", "yes_by_source_design", "no", "source=Abstract/Results; p-values only", "not_usable", "Published PubMed/Open Access p-values. No sample size/effect size for D and no main-treatment flag.",
  "JagerLeek", "biomedicine", "no", "yes_by_source_design", "no", "title-based crude RCT flag only; p-values only", "not_usable", "Published top-medical-journal abstract p-values. No D and no treatment/main-outcome flag.",
  "ManyLabs2", "psychology", "yes", "no_replication_results", "yes_replication_effect", "metaid=experiment; rows are replications", "not_published_papers_but_good_sanity_check", "Replication corpus, not original published-paper corpus. Excellent sanity check for realistic D distribution.",
  "Metapsy", "psychotherapy", "yes", "partial_by_database_design", "partial", "method=RCT; measure; metaid=database; no publication-status flag", "usable_with_caveats", "Psychotherapy RCT database with Hedges g/SMD. Treatment domain coherent, but no published-only flag or one focal endpoint flag.",
  "Nuijten", "intelligence", "yes", "partial_by_source_design", "no", "none beyond dataset", "weak_for_target", "Intelligence meta-meta-analysis; D is native package effect. Not a treatment/main-effect corpus.",
  "OSC", "psychology", "yes", "no_replication_results", "yes_replication_effect", "rows are replication outcomes", "not_published_papers_but_good_sanity_check", "Open Science Collaboration replication rows, not original published paper claims.",
  "psymetadata", "psychology", "yes", "partial_by_source_design", "mixed", "subset=source meta-analysis dataset", "weak_for_target", "Curated psychology meta-analysis datasets. Good D coverage, but heterogeneous constructs and no published-only/focal-treatment flags.",
  "Sladekova", "psychology", "yes", "partial_by_source_design", "no", "metaid; Fisher-z style effects", "weak_for_target", "Psychology meta-analytic effects; D from Fisher z conversion. No treatment of interest or published-only primary-row filter.",
  "WWC", "education", "yes", "partial_clearinghouse_reports", "partial_intervention_findings", "method=RCT/quasi; subset=Outcome_Domain", "usable_with_caveats", "Education intervention findings with study design and domains. Not journal-paper-only and may include many outcomes per study.",
  "Yang", "ecology & evolution", "yes", "partial_by_source_design", "no", "measure; no publication-status or focal-treatment flag", "weak_for_target", "Ecology/evolution meta-analysis rows. Not treatment of interest; some overlap with Costello/Fox pipeline."
)

audit <- manual %>%
  left_join(row_counts, by = "dataset") %>%
  left_join(d_counts, by = "dataset") %>%
  left_join(d_summary, by = "dataset") %>%
  mutate(
    d_rows = coalesce(d_rows, 0L),
    d_coverage = d_rows / bear_rows,
    can_calculate_D = case_when(
      d_rows == 0 ~ "no",
      d_rows == bear_rows ~ "yes_all_rows",
      d_rows / bear_rows >= 0.8 ~ "yes_most_rows",
      TRUE ~ "partial"
    )
  ) %>%
  select(
    dataset, domain, bear_rows, d_rows, d_coverage, can_calculate_D, d_verdict,
    median_D, p90_D, median_ss, d_sources,
    published_paper_isolation, treatment_interest_isolation,
    best_filter_in_bear, published_treatment_d_grade, notes
  ) %>%
  arrange(published_treatment_d_grade, dataset)

write_csv(audit, file.path(out_dir, "bear_corpus_tractability_audit.csv"))

fmt <- function(x) {
  ifelse(is.na(x), "", formatC(x, format = "fg", digits = 4))
}

md_table <- function(df) {
  lines <- c(
    paste0("| ", paste(names(df), collapse = " | "), " |"),
    paste0("| ", paste(rep("---", ncol(df)), collapse = " | "), " |")
  )
  for (i in seq_len(nrow(df))) {
    vals <- vapply(df[i, ], function(x) {
      val <- x[[1]]
      if (is.numeric(val)) fmt(val) else as.character(val)
    }, character(1))
    lines <- c(lines, paste0("| ", paste(vals, collapse = " | "), " |"))
  }
  paste(lines, collapse = "\n")
}

compact <- audit %>%
  transmute(
    dataset,
    D = can_calculate_D,
    D_coverage = d_coverage,
    median_D,
    published = published_paper_isolation,
    treatment = treatment_interest_isolation,
    grade = published_treatment_d_grade,
    filter = best_filter_in_bear
  )

md <- c(
  "# BEAR Corpus Tractability Audit",
  "",
  "Question: for each BEAR corpus, can we calculate a Cohen-d-like `D`, and can BEAR isolate a published-paper treatment-of-interest slice?",
  "",
  "Grades:",
  "",
  "- `best_available_in_bear`: closest to published-source plus main-treatment/outcome inside BEAR.",
  "- `usable_with_caveats`: useful treatment/intervention corpus, but not strict published journal rows or not strict one focal outcome.",
  "- `not_published_papers_but_good_toi`: treatment/outcome is good, but source is registry or replication rather than published papers.",
  "- `weak_for_target`: D may exist, but the corpus is not a clean published-paper treatment-of-interest object.",
  "- `not_usable` / `not_usable_without_raw_inputs`: BEAR alone is missing D or missing the needed source/treatment fields.",
  "",
  "## Compact Table",
  "",
  md_table(compact),
  "",
  "## Full Notes",
  "",
  md_table(audit %>% select(dataset, d_sources, notes)),
  ""
)

writeLines(md, file.path(out_dir, "bear_corpus_tractability_audit.md"))

message("Wrote ", file.path(out_dir, "bear_corpus_tractability_audit.csv"))
message("Wrote ", file.path(out_dir, "bear_corpus_tractability_audit.md"))
