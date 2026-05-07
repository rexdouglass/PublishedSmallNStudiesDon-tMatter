# Figure 1 Coverage and Loss Accounting

Date: 2026-05-04

## Definitions

- A source/corpus record is a discovered paper, database, project, repository, package, or registry-like object in the intake table.
- A row-grain object is a local unit that could plausibly become one original-vs-replication or original-vs-follow-up comparison row.
- Figure 1A means the strict direct D/N panel.
- Figure 1B means the alternative D-equivalent clinical/binary panel.
- Native retention means values are kept on their native scale because forcing them onto D would be misleading.
- Denominator-only means the object supports a coverage statement but is not currently a plotted quantitative row.

## Headline Accounting

The current local accounted row-grain universe is **3,316** objects. Of those, **1,684** rows (**50.8%**) pass the strict Figure 1A D/N gate. The root table already contains D/N values for **2,436** rows (**73.5%**) when current-rule blocked D/N rows are counted as audited value-bearing material. Across strict Figure 1A, Figure 1B D-equivalent, and native-scale retention, **1,863** rows (**56.2%**) can be shown in some x/y quantitative panel without using currently blocked D/N rows. If currently blocked D/N rows are counted as value-bearing but not main-panel eligible, **2,615** rows (**78.9%**) have values and N in hand. The remaining **701** rows (**21.1%**) are retained only as denominator, duplicate-risk, parser-repair, or missing-value evidence.

At the source/corpus level, the intake table contains **448** source/corpus records, including **261** marked Figure 1 relevant. The alternate-route recheck covered **79** rejected or blocked records: **33** gained an alternate route and **46** remained context-only or rejected with no supported subplot route.

This supports a coverage claim about the public, locally discovered, and mirrorable many-replication corpus universe. It should not be phrased as all possible science-wide follow-up studies, because request-only clinical datasets and one-off paper mining remain outside this local row denominator.

## Row Disposition

| disposition_label | row_count | percent_of_accounted_row_grain_universe | usable_for | definition |
| --- | --- | --- | --- | --- |
| Strict Figure 1A direct D/N rows | 1684 | 50.8 | main Figure 1A | Rows included by the current strict Figure 1 D/N plot rule. |
| D/N rows blocked by current Figure 1A rule | 752 | 22.7 | denominator, rule audit, robustness checks | Root rows have D_original, D_replication, N_original, and N_replication but fail a current plot gate. |
| Comparative binary rows with D-equivalent conversion | 88 | 2.7 | Figure 1B diagnostic | Active/control count rows can be converted by log(OR) * sqrt(3) / pi. |
| Native-effect rows not on D axis | 91 | 2.7 | native-scale diagnostic, not common-D plot | Response-rate or similar rows with original/follow-up values and N but no defensible D conversion. |
| Pair roster only, public values unavailable | 248 | 7.5 | coverage denominator only | Rows identify original/follow-up linkage but public/local bytes do not expose effect and N values. |
| Effect present, N missing | 172 | 5.2 | repair queue and denominator | Public result rows expose effect-like values but no original/follow-up sample-size columns. |
| Parsed row grain, no copied effect/N evidence | 271 | 8.2 | denominator with parser caveat | A parser found row-grain records, but current extraction did not copy effect or N evidence. |
| D/N-looking rows with duplicate risk | 10 | 0.3 | coverage denominator until deduped | Candidate D/N-looking rows exist, but they overlap heavily with already harvested sources. |

## Stage Summary

| stage_id | count | count_type | percent_of_accounted_row_grain_universe | meaning |
| --- | --- | --- | --- | --- |
| accounted_row_grain_universe | 3316 | row-grain objects | 100.0 | Working local denominator after adding alternate routes and explicit failure buckets. |
| strict_figure1a_current | 1684 | rows | 50.8 | Rows that hit the current strict direct-D/N Figure 1A gate. |
| root_dn_any_current_status | 2436 | rows | 73.5 | Rows with D/N in the root table, whether current-rule included or blocked. |
| value_bearing_any_axis_or_blocked | 2615 | rows | 78.9 | Rows with D, D-equivalent, or native values and N, including strict-rule blocked D/N rows. |
| quantitative_or_native_xy_not_counting_blocked_dn | 1863 | rows | 56.2 | Rows that can appear in Figure 1A, Figure 1B, or a native-scale panel without using currently blocked D/N rows. |
| denominator_or_repair_only | 701 | rows | 21.1 | Rows retained only as denominator, duplicate-risk, parser-repair, or missing-value evidence. |
| root_source_records_all | 448 | source/corpus records |  | All consolidated source/corpus/database records in CORPORA_AND_DATABASES.tsv. |
| root_source_records_figure1_relevant_yes | 261 | source/corpus records |  | Records explicitly marked relevant to the Figure 1 replication-pair universe. |
| rechecked_records_with_alternate_route | 33 | source/corpus records |  | Previously rejected/blocked records that now have a non-Figure-1A route. |
| rechecked_records_no_supported_subplot_route | 46 | source/corpus records |  | Previously rejected/blocked records still lacking any supported alternate subplot route. |

## Source/Candidate Status

| status_bucket | source_record_count | row_count_if_applicable | accounting_use |
| --- | --- | --- | --- |
| root_source_records_all | 448 |  | source-level universe only; not a row denominator |
| root_source_records_figure1_relevant_yes | 261 |  | source-level coverage scope |
| metadata_only_search_hits | 137 |  | loss reason: no local/public value object |
| parser_not_implemented | 12 |  | technical repair queue |
| conversion_policy_missing | 6 |  | methodology gate |
| raw_viability_parent_families_checked | 16 |  | mirror/local-byte coverage |
| raw_viability_candidate_for_mapping | 2 | 421 | future source_result mapping |
| rechecked_records_with_alternate_route | 33 | 1632 | alternative subplot or denominator |
| rechecked_records_no_supported_subplot_route | 46 | 0 | context/exclusion evidence |
| alternate_route::remain_context_or_rejected_no_alternate_subplot::no_worklist | 46 | 0 | no alternate plot universe |
| alternate_route::route_to_coverage_denominator_catalog::missing_n_or_value_repair_worklist | 14 | 271 | plot1d_source_object_coverage_denominator |
| alternate_route::route_to_coverage_denominator_catalog::no_worklist | 5 | 1010 | plot1d_source_object_coverage_denominator |
| alternate_route::route_to_d_equivalent_diagnostic_worklist::no_worklist | 1 | 88 | plot1b_clinical_binary_d_equivalent |
| alternate_route::route_to_missing_value_repair_worklist::missing_n_or_value_repair_worklist | 7 | 172 | plot1d_source_object_coverage_denominator |
| alternate_route::route_to_native_effect_diagnostic_worklist::no_worklist | 6 | 91 | plot1c_native_effect_retention |

## Main Loss Reasons

- Current-rule gate failure: D/N exists, but the row does not pass the strict Figure 1A inclusion rule.
- Metric gate failure: native response/proportion rows have values and N but no defensible D conversion.
- Public-value gap: pair rosters identify original/follow-up links, but public bytes do not expose row-level effect and N.
- Missing-N gap: effects are public, but sample sizes are not in the mirrored result tables.
- Parser gap: row-grain records were parsed, but effect/N evidence was not copied.
- Duplicate-risk gap: D/N-looking rows exist but likely overlap with FReD/current rows and need dedupe before promotion.
- Context-only/exclusion: source records are replication-adjacent but do not expose a supported row route for Figure 1A, Figure 1B, native retention, or denominator accounting.

## Generated Artifacts

- `steps/corpus_results/figure1/coverage_loss_accounting/figure1-row-disposition.tsv`
- `steps/corpus_results/figure1/coverage_loss_accounting/figure1-source-coverage-status.tsv`
- `steps/corpus_results/figure1/coverage_loss_accounting/figure1-coverage-loss-stages.tsv`
- `steps/corpus_results/figure1/coverage_loss_accounting/figure1-coverage-loss-bars.png`
