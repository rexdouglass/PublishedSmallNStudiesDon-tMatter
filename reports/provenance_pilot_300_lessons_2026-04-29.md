# 300-Row Provenance Pilot Lessons

Date: 2026-04-29

## What Changed

The provenance pilot now samples 300 plotted rows by default. The Makefile exposes `SCHEMA_PILOT_N` and `SCHEMA_PILOT_SEED`, so quick debugging can still use smaller samples without changing code.

The pilot now runs:

```sh
make schema-pilot
make validate-schema-pilot
```

Primary outputs:

- `data/derived/effect_inflation_dataset/schema_pilot/source_result_codebook_sample_300.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/human_check_source_result_sample_300.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/real_world_grounding_sample_300.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/real_world_grounding_below_level3_sample_300.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/codebook_validation_report.md`

## Evidence-Level Results

| Minimum evidence level | Rows | Percent |
|---:|---:|---:|
| 0 | 300 | 100.0% |
| 1 | 300 | 100.0% |
| 2 | 300 | 100.0% |
| 3 | 285 | 95.0% |
| 4 | 285 | 95.0% |
| 5 | 43 | 14.3% |
| 6 | 37 | 12.3% |
| 7 | 0 | 0.0% |

Level counts:

| Level | Name | Rows |
|---:|---|---:|
| 2 | external_source_assertion | 15 |
| 4 | target_source_independently_grounded | 242 |
| 5 | original_source_obtained | 6 |
| 6 | original_number_extracted | 37 |

The practical current plotting floor should be evidence level 3: at minimum, an external corpus/source assertion with an identified represented paper/study/trial/source. Levels 0-2 should be treated as audit/worklist rows, not public dots.

Under the stricter ladder, level 3 requires the corpus/source row to name enough bibliographic or registry information that the target source could theoretically be found. Level 4 means that target source has been independently grounded in the wider world via DOI, PMID, PMCID, NCT, AEA, Dataverse, Crossref, another citation database, or a stable independent URL. Level 5 means the original source object or bytes were actually obtained or mirrored locally. Level 6 means the exact effect/N values were extracted by us from that original or authoritative source object.

## What Worked

- The retrace recovered every sampled plotted row.
- All 300 sampled rows have local ultimate source paths.
- 298/300 rows have recovered upstream effect/statistic text.
- 300/300 rows have recovered upstream N text.
- 285/300 rows can now be tied to an identified represented source at level 4 or higher.
- Source-specific resolvers matter: the label-title Crossref fallback, Button/Nord PMC reference-list lookup, and Boyce target-ID mappings moved 14 additional rows to level 3+.
- The stricter level-4 rule grounds high-confidence represented-source URLs without pretending the numbers themselves are original-source verified.

## What Is Still Hard

The 15 rows below level 4 are not generic extraction failures:

| Source family | Rows | Reason |
|---|---:|---|
| Schäfer/Schwarz psychology articles without preregistration | 5 | Mirrored workbook exposes anonymized IDs such as `schaefer_2019_np_*`, but no article title, DOI, PMID, or URL. |
| Schäfer/Schwarz 2019 preregistered psychology articles | 4 | Mirrored workbook exposes anonymized preregistered study indices, but no article crosswalk. |
| `schaefer_schwarz_2019_without_prereg` | 3 | Same anonymized-ID problem. |
| Schäfer/Schwarz preregistered psychology articles | 1 | Same anonymized-ID problem. |
| `linden_2024_random_effects` | 2 | Mirrored SAV exposes `linden_YEAR_index` handles without a public article-key crosswalk. |

These rows should not be promoted unless we obtain the author/codebook crosswalk or a supplementary file that maps the anonymized IDs to real papers. Under the stricter rule, an external corpus assertion without enough information to identify the target source remains level 2, not level 3.

## Validation Status

The formal codebook validation is intentionally strict. It still reports high issues for two sampled rows without upstream effect text, one high issue for missing source locators, and one medium issue because 262/300 rows are correctly marked `coded_with_schema_gaps`. That is a useful failure mode: the tables are structurally valid, but only 38 sampled source-result rows are fully coded under the current exact-number/original-source standard.

## Strategy Implications

1. Do not spend broad scraping time on anonymized corpus rows until the crosswalk exists. They cannot honestly clear level 3 from public row IDs alone.
2. Add source-specific resolvers for recurring corpus formats. Small deterministic mappings produced measurable gains.
3. Write source-result rows at extraction time, before corpus/paper median collapse. Retrofitting provenance after aggregation is much slower.
4. For public plots, filter to evidence level >= 3 once the full dot table has provenance coverage.
5. For publication-grade claims, continue pushing rows to level >= 5 by obtaining the original source object, and to level >= 6 by checking the exact number in that source.
