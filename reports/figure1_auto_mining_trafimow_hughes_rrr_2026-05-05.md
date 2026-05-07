# Trafimow/Hughes RRR Auto-Mining Recompute

This artifact recomputes the exact word-generation replication contrast from the locally mirrored OSF package for Rife et al. (2025), the Registered Replication Report of Study 3 from Trafimow and Hughes (2012).

## Source Objects

- Raw OSF files: `data/raw/replication_projects/individual_search_batch006/api_candidate_410ff1685532db83/osf_atc39_data`
- Lab effects TSV: `steps/individual_replication_papers/figure1/auto_mining/trafimow_hughes_rrr_lab_effects.tsv`
- Summary TSV: `steps/individual_replication_papers/figure1/auto_mining/trafimow_hughes_rrr_summary.tsv`
- Input manifest TSV: `steps/individual_replication_papers/figure1/auto_mining/trafimow_hughes_rrr_input_files.tsv`

## Recomputed Focal Values

- Focal analyzed N from mirrored word-generation participant files, excluding METAlab: 1672 (383 death/no-delay; 1289 all other conditions).
- Participant-pooled raw mean difference: 0.218932 death-related words.
- Participant-pooled Cohen d: 0.274585.
- Lab random-effects raw mean difference: 0.129050, SE 0.039941, 95% CI [0.050767, 0.207334], k = 20.
- Lab random-effects Cohen d: 0.430033, SE 0.084823, 95% CI [0.263780, 0.596285], k = 20.
- Article reported raw mean difference 0.08 standardized by recomputed participant-pooled SD: d = 0.100336.
- Article Table 4 random-effects raw mean difference using recomputed focal Ns: 0.071977, SE 0.031396, 95% CI [0.010440, 0.133513], k = 19.
- Article Table 4 random-effects Cohen d using recomputed focal Ns: 0.327486, SE 0.083579, 95% CI [0.163672, 0.491301], k = 19.
- Article Table 4 participant-pooled Cohen d using recomputed focal Ns: 0.206858.

## Figure 1 Promotion Status

This recomputation resolves the local raw-data path but does not by itself choose the final plotted D. The most direct D-scale reconstruction is `article_table4_lab_random_effects_smd`; the more conservative hybrid sensitivity is the article-reported raw mean difference standardized by the recomputed pooled SD.

## Method Notes

- The participant filters mirror the downloaded `Analyses.R` plan as closely as possible from the downloaded files: manual exclusion decisions where completed coding files provide them, complete Gender/Age, `Understand == 0`, `interviewtime > 300`, word-generation task only, and METAlab excluded for the exact word-generation replication.
- Blank coding-file decisions are treated as non-exclusions because the downloaded coding files are mostly placeholder exports.
- BYUI appears in the article table but no BYUI main participant CSV was available through the mirrored OSF package, so article-table reconstructions using raw focal Ns exclude BYUI.
- Lab rows written: 20.
