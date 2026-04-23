#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(dplyr)
  library(readr)
})

args <- commandArgs(trailingOnly = TRUE)
bear_path <- if (length(args) >= 1) args[[1]] else "data/raw/bear/BEAR.rds"
out_dir <- if (length(args) >= 2) args[[2]] else "data/derived/bear"

dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

dataset_domain <- c(
  ArelBundock = "political science",
  Askarov = "economics",
  Bartos = "exercise",
  BarnettWren = "biomedicine",
  Brodeur = "economics",
  Chavalarias = "biomedicine",
  clinicaltrials = "clinical trials",
  Cochrane = "medicine & health",
  CostelloFox = "ecology & evolution",
  euctr = "clinical trials",
  Head = "biomedicine",
  JagerLeek = "biomedicine",
  ManyLabs2 = "psychology",
  Metapsy = "psychotherapy",
  Nuijten = "intelligence",
  OSC = "psychology",
  psymetadata = "psychology",
  Sladekova = "psychology",
  WWC = "education",
  Yang = "ecology & evolution"
)

dataset_class <- c(
  ArelBundock = "meta",
  Askarov = "meta",
  Bartos = "meta",
  BarnettWren = "scrape",
  Brodeur = "curated",
  Chavalarias = "scrape",
  clinicaltrials = "curated",
  Cochrane = "meta",
  CostelloFox = "meta",
  euctr = "curated",
  Head = "scrape",
  JagerLeek = "scrape",
  ManyLabs2 = "replications",
  Metapsy = "meta",
  Nuijten = "curated",
  OSC = "replications",
  psymetadata = "curated",
  Sladekova = "meta",
  WWC = "curated",
  Yang = "meta"
)

dataset_label <- c(
  ArelBundock = "Arel-Bundock et al",
  Askarov = "Askarov et al",
  Bartos = "Bartos et al",
  BarnettWren = "Barnett and Wren",
  Brodeur = "Brodeur et al",
  Chavalarias = "Chavalarias et al",
  clinicaltrials = "clinicaltrials.gov",
  Cochrane = "Cochrane",
  CostelloFox = "Costello and Fox",
  euctr = "EUDRA",
  Head = "Head et al",
  JagerLeek = "Jager and Leek",
  ManyLabs2 = "Many Labs 2",
  Metapsy = "Metapsy",
  Nuijten = "Nuijten et al",
  OSC = "OpenSciCollab",
  psymetadata = "psymetadata",
  Sladekova = "Sladekova et al",
  WWC = "What Works Clearing.",
  Yang = "Yang et al"
)

clean_chr <- function(x) {
  x <- as.character(x)
  x[is.na(x) | x == ""] <- "(missing)"
  x
}

safe_div <- function(a, b) {
  out <- a / b
  out[!is.finite(out)] <- NA_real_
  out
}

summarise_d <- function(data) {
  data %>%
    summarise(
      n_rows = n(),
      n_studies = n_distinct(study_key[!is.na(studyid) & studyid != ""]),
      n_meta = n_distinct(meta_key[!is.na(metaid) & metaid != ""]),
      median_D = median(D_abs_best, na.rm = TRUE),
      mean_D = mean(D_abs_best, na.rm = TRUE),
      p75_D = quantile(D_abs_best, 0.75, na.rm = TRUE, names = FALSE),
      p90_D = quantile(D_abs_best, 0.90, na.rm = TRUE, names = FALSE),
      p95_D = quantile(D_abs_best, 0.95, na.rm = TRUE, names = FALSE),
      pct_D_lt_0_2 = mean(D_abs_best < 0.2, na.rm = TRUE),
      pct_D_ge_0_2 = mean(D_abs_best >= 0.2, na.rm = TRUE),
      pct_D_ge_0_5 = mean(D_abs_best >= 0.5, na.rm = TRUE),
      pct_D_ge_0_8 = mean(D_abs_best >= 0.8, na.rm = TRUE),
      pct_D_ge_1_0 = mean(D_abs_best >= 1.0, na.rm = TRUE),
      pct_D_ge_2_0 = mean(D_abs_best >= 2.0, na.rm = TRUE),
      median_ss = median(ss, na.rm = TRUE),
      pct_abs_z_ge_1_96 = mean(abs_z >= 1.96, na.rm = TRUE),
      .groups = "drop"
    )
}

format_num <- function(x, digits = 4) {
  ifelse(is.na(x), "", formatC(x, format = "fg", digits = digits))
}

markdown_table <- function(data, n = 25) {
  if (nrow(data) == 0) return("_No rows._")
  show <- head(data, n)
  lines <- c(
    paste0("| ", paste(names(show), collapse = " | "), " |"),
    paste0("| ", paste(rep("---", length(show)), collapse = " | "), " |")
  )
  for (i in seq_len(nrow(show))) {
    vals <- vapply(show[i, ], function(x) {
      x <- x[[1]]
      if (is.numeric(x)) format_num(x) else as.character(x)
    }, character(1))
    lines <- c(lines, paste0("| ", paste(vals, collapse = " | "), " |"))
  }
  paste(lines, collapse = "\n")
}

message("Reading BEAR: ", bear_path)
bear <- readRDS(bear_path)

message("Computing D fields")
measure_lower <- tolower(as.character(bear$measure))
measure_lower[is.na(measure_lower)] <- ""

standardized_measure <- grepl("smd|hedge|cohen", measure_lower)
standardized_dataset <- bear$dataset %in% c("Bartos", "Metapsy", "ManyLabs2", "Nuijten", "psymetadata", "WWC")
fisher_z_measure <- measure_lower == "zr"
latent_probit_measure <- measure_lower == "probit"
ratio_measure <- measure_lower %in% c("ratio", "odds ratio", "risk ratio", "hazard ratio", "geometric ratio", "ratio/other ratio")

b <- suppressWarnings(as.numeric(bear$b))
z <- suppressWarnings(as.numeric(bear$z))
ss <- suppressWarnings(as.numeric(bear$ss))
se <- suppressWarnings(as.numeric(bear$se))

D_standardized <- ifelse((standardized_measure | standardized_dataset) & is.finite(b), abs(b), NA_real_)

r_from_zr <- tanh(b)
D_fisher_z <- ifelse(
  fisher_z_measure & is.finite(r_from_zr) & abs(r_from_zr) < 0.999999,
  abs(2 * r_from_zr / sqrt(1 - r_from_zr^2)),
  NA_real_
)

D_log_ratio <- ifelse(
  ratio_measure & is.finite(b),
  abs(b) * sqrt(3) / pi,
  NA_real_
)

D_latent_probit <- ifelse(latent_probit_measure & is.finite(b), abs(b), NA_real_)
D_z_n_proxy <- ifelse(is.finite(z) & is.finite(ss) & ss > 0, 2 * abs(z) / sqrt(ss), NA_real_)

D_abs_best <- D_standardized
d_source <- ifelse(!is.na(D_abs_best), "standardized_or_package_effect_b", NA_character_)

fill <- is.na(D_abs_best) & !is.na(D_fisher_z)
D_abs_best[fill] <- D_fisher_z[fill]
d_source[fill] <- "fisher_z_to_d"

fill <- is.na(D_abs_best) & !is.na(D_log_ratio)
D_abs_best[fill] <- D_log_ratio[fill]
d_source[fill] <- "log_ratio_to_d_chinn_approx"

fill <- is.na(D_abs_best) & !is.na(D_latent_probit)
D_abs_best[fill] <- D_latent_probit[fill]
d_source[fill] <- "latent_probit_effect_b"

fill <- is.na(D_abs_best) & !is.na(D_z_n_proxy)
D_abs_best[fill] <- D_z_n_proxy[fill]
d_source[fill] <- "z_n_proxy_2absz_sqrtN"

domain <- unname(dataset_domain[as.character(bear$dataset)])
domain[is.na(domain)] <- "(missing)"
corpus_class <- unname(dataset_class[as.character(bear$dataset)])
corpus_class[is.na(corpus_class)] <- "(missing)"
dataset_name <- unname(dataset_label[as.character(bear$dataset)])
dataset_name[is.na(dataset_name)] <- as.character(bear$dataset)

year <- suppressWarnings(as.numeric(bear$year))
abs_z <- abs(z)
year_band <- cut(
  year,
  breaks = c(-Inf, 1989, 1999, 2009, 2019, Inf),
  labels = c("<1990", "1990s", "2000s", "2010s", "2020+"),
  right = TRUE
)
year_band <- as.character(year_band)
year_band[is.na(year_band)] <- "(missing)"

ss_band <- cut(
  ss,
  breaks = c(-Inf, 19, 49, 99, 299, 999, 9999, Inf),
  labels = c("<20", "20-49", "50-99", "100-299", "300-999", "1k-9,999", "10k+"),
  right = TRUE
)
ss_band <- as.character(ss_band)
ss_band[is.na(ss_band)] <- "(missing)"

z_band <- cut(
  abs_z,
  breaks = c(-Inf, 1, 1.96, 3, 5, Inf),
  labels = c("<1", "1-1.96", "1.96-3", "3-5", "5+"),
  right = FALSE
)
z_band <- as.character(z_band)
z_band[is.na(z_band)] <- "(missing)"

d_values <- tibble(
  row_id = seq_len(nrow(bear)),
  dataset = as.character(bear$dataset),
  dataset_name = dataset_name,
  domain = domain,
  corpus_class = corpus_class,
  metaid = as.character(bear$metaid),
  studyid = as.character(bear$studyid),
  method = clean_chr(bear$method),
  measure = clean_chr(bear$measure),
  field = clean_chr(bear$field),
  subset = clean_chr(bear$subset),
  group = clean_chr(bear$group),
  source = clean_chr(bear$source),
  year = year,
  year_band = year_band,
  ss = ss,
  ss_band = ss_band,
  z = z,
  abs_z = abs_z,
  z_band = z_band,
  b = b,
  se = se,
  D_abs_best = D_abs_best,
  D_best_source = ifelse(is.na(d_source), "(missing)", d_source),
  D_abs_standardized = D_standardized,
  D_abs_fisher_z_to_d = D_fisher_z,
  D_abs_log_ratio_chinn = D_log_ratio,
  D_abs_latent_probit = D_latent_probit,
  D_abs_z_n_proxy = D_z_n_proxy,
  study_key = ifelse(is.na(bear$studyid) | bear$studyid == "", NA_character_, paste(bear$dataset, bear$studyid, sep = "::")),
  meta_key = ifelse(is.na(bear$metaid) | bear$metaid == "", NA_character_, paste(bear$dataset, bear$metaid, sep = "::"))
) %>%
  filter(!is.na(D_abs_best))

message("Rows with a computable D: ", format(nrow(d_values), big.mark = ","))
write_csv(d_values, file.path(out_dir, "bear_d_values.csv.gz"))

message("Summarizing by dataset and D source")
overall <- d_values %>%
  summarise_d() %>%
  mutate(summary = "overall", value = "all", .before = 1)

dataset_summary <- d_values %>%
  group_by(dataset, dataset_name, domain, corpus_class) %>%
  summarise_d() %>%
  arrange(median_D)

d_source_summary <- d_values %>%
  group_by(D_best_source) %>%
  summarise_d() %>%
  arrange(median_D)

write_csv(dataset_summary, file.path(out_dir, "bear_d_dataset_summary.csv"))
write_csv(d_source_summary, file.path(out_dir, "bear_d_source_summary.csv"))

covariates <- c(
  "dataset", "dataset_name", "domain", "corpus_class", "D_best_source",
  "method", "measure", "field", "subset", "group", "source",
  "year_band", "ss_band", "z_band"
)

message("Summarizing one-way covariates")
one_way <- bind_rows(lapply(covariates, function(cv) {
  d_values %>%
    group_by(.data[[cv]]) %>%
    summarise_d() %>%
    mutate(covariate = cv, level = as.character(.data[[cv]]), .before = 1) %>%
    select(covariate, level, everything(), -all_of(cv))
})) %>%
  filter(n_rows >= 20) %>%
  arrange(covariate, median_D)

write_csv(one_way, file.path(out_dir, "bear_d_covariate_medians.csv"))

message("Summarizing pairwise covariates")
pair_covariates <- c(
  "dataset", "domain", "corpus_class", "D_best_source", "method",
  "measure", "subset", "group", "source", "year_band", "ss_band", "z_band"
)

pairs <- combn(pair_covariates, 2, simplify = FALSE)
pairwise <- bind_rows(lapply(pairs, function(cvs) {
  cv1 <- cvs[[1]]
  cv2 <- cvs[[2]]
  d_values %>%
    group_by(.data[[cv1]], .data[[cv2]]) %>%
    summarise_d() %>%
    mutate(
      covariate_1 = cv1,
      level_1 = as.character(.data[[cv1]]),
      covariate_2 = cv2,
      level_2 = as.character(.data[[cv2]]),
      .before = 1
    ) %>%
    select(covariate_1, level_1, covariate_2, level_2, everything(), -all_of(c(cv1, cv2)))
})) %>%
  filter(n_rows >= 50) %>%
  arrange(covariate_1, covariate_2, median_D)

write_csv(pairwise, file.path(out_dir, "bear_d_pairwise_covariate_medians.csv"))

message("Writing compact high/low tables")
lowest_dataset <- dataset_summary %>% arrange(median_D) %>% head(25)
highest_dataset <- dataset_summary %>% arrange(desc(median_D)) %>% head(25)

lowest_one_way <- one_way %>%
  filter(n_rows >= 500) %>%
  arrange(median_D) %>%
  head(50)

highest_one_way <- one_way %>%
  filter(n_rows >= 500) %>%
  arrange(desc(median_D)) %>%
  head(50)

lowest_pairwise <- pairwise %>%
  filter(n_rows >= 500) %>%
  arrange(median_D) %>%
  head(75)

highest_pairwise <- pairwise %>%
  filter(n_rows >= 500) %>%
  arrange(desc(median_D)) %>%
  head(75)

write_csv(lowest_one_way, file.path(out_dir, "bear_d_lowest_covariate_medians.csv"))
write_csv(highest_one_way, file.path(out_dir, "bear_d_highest_covariate_medians.csv"))
write_csv(lowest_pairwise, file.path(out_dir, "bear_d_lowest_pairwise_medians.csv"))
write_csv(highest_pairwise, file.path(out_dir, "bear_d_highest_pairwise_medians.csv"))

message("Writing markdown summary")
md <- c(
  "# BEAR D Value Summary",
  "",
  paste0("Input rows: ", format(nrow(bear), big.mark = ","), "."),
  paste0("Rows with computable `D_abs_best`: ", format(nrow(d_values), big.mark = ","), "."),
  "",
  "## D Definitions",
  "",
  "`D_abs_best` is an absolute, Cohen-d-like effect magnitude where BEAR has enough information. It is selected in this order:",
  "",
  "1. `standardized_or_package_effect_b`: `abs(b)` for SMD/Hedges/Cohen measures and package datasets whose `b` is already an effect size.",
  "2. `fisher_z_to_d`: Fisher z/correlation effects converted by `r = tanh(b)`, `d = 2r / sqrt(1-r^2)`.",
  "3. `log_ratio_to_d_chinn_approx`: ratio/log-ratio effects converted by `d ~= log(ratio) * sqrt(3) / pi`.",
  "4. `latent_probit_effect_b`: Cochrane dichotomous probit-scale effects, kept as a latent standardized effect.",
  "5. `z_n_proxy_2absz_sqrtN`: broad fallback `2|z|/sqrt(N)` when sample size exists.",
  "",
  "Rows with p-values/z-values only and no sample size cannot be converted to D. That excludes most Chavalarias, Head, and Jager-Leek rows.",
  "",
  "## Overall",
  "",
  markdown_table(overall %>% select(summary, value, n_rows, n_studies, median_D, p90_D, pct_D_ge_0_5, pct_D_ge_0_8, pct_D_ge_1_0, pct_D_ge_2_0), n = 10),
  "",
  "## By D Source",
  "",
  markdown_table(d_source_summary %>% select(D_best_source, n_rows, n_studies, median_D, p90_D, pct_D_ge_0_5, pct_D_ge_0_8, pct_D_ge_1_0, pct_D_ge_2_0), n = 20),
  "",
  "## Datasets With Lowest Median D",
  "",
  markdown_table(lowest_dataset %>% select(dataset, domain, corpus_class, n_rows, n_studies, median_D, p90_D, pct_D_ge_0_5, pct_D_ge_0_8, pct_D_ge_1_0), n = 25),
  "",
  "## Datasets With Highest Median D",
  "",
  markdown_table(highest_dataset %>% select(dataset, domain, corpus_class, n_rows, n_studies, median_D, p90_D, pct_D_ge_0_5, pct_D_ge_0_8, pct_D_ge_1_0), n = 25),
  "",
  "## Lowest Large-N Covariate Groups",
  "",
  markdown_table(lowest_one_way %>% select(covariate, level, n_rows, n_studies, median_D, p90_D, pct_D_ge_0_5, pct_D_ge_0_8, pct_D_ge_1_0), n = 30),
  "",
  "## Highest Large-N Covariate Groups",
  "",
  markdown_table(highest_one_way %>% select(covariate, level, n_rows, n_studies, median_D, p90_D, pct_D_ge_0_5, pct_D_ge_0_8, pct_D_ge_1_0), n = 30),
  "",
  "## Notes",
  "",
  "- Do not read `D_abs_best` as a perfectly harmonized true Cohen's d across every corpus. It is a best-effort effect-size magnitude with its derivation recorded in `D_best_source`.",
  "- For strict continuous standardized effects, filter `D_best_source == 'standardized_or_package_effect_b'` and measures/datasets you trust.",
  "- For Figure-2-style boundary work, use `D_abs_z_n_proxy` or `D_best_source == 'z_n_proxy_2absz_sqrtN'` and inspect sample-size assumptions.",
  ""
)

writeLines(md, file.path(out_dir, "bear_d_summary.md"))

message("Done")
message("Wrote: ", file.path(out_dir, "bear_d_values.csv.gz"))
message("Wrote: ", file.path(out_dir, "bear_d_dataset_summary.csv"))
message("Wrote: ", file.path(out_dir, "bear_d_covariate_medians.csv"))
message("Wrote: ", file.path(out_dir, "bear_d_pairwise_covariate_medians.csv"))
message("Wrote: ", file.path(out_dir, "bear_d_summary.md"))
