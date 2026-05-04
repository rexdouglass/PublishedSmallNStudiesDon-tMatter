# Figure 1 Search Recall Audit

This diagnostic checks whether saved Figure 1 search manifests rediscover known-good Figure 1 source collections.

Definitions:

- Known-good source: an included Plot 1 source-family/source-table row with at least one kept Figure 1 pair.
- Rediscovered: a saved `corporasearch-*.json` row matched the known source by DOI, URL, alias, or distinctive token overlap.
- Weak match: matched only by low-specificity token overlap and should be manually checked.
- Missed: no saved search manifest row matched the known source.
- Internal support source: a hand-built/local audit artifact that is useful for Figure 1 but is not expected to be rediscovered by external search.

## Summary

| Metric | Value |
| --- | ---: |
| known_good_sources | 66 |
| rediscovered_sources | 65 |
| weak_match_sources | 0 |
| missed_sources | 1 |
| source_recall_percent | 98.5 |
| external_searchable_sources | 65 |
| external_searchable_rediscovered_sources | 65 |
| external_searchable_missed_sources | 0 |
| external_searchable_source_recall_percent | 100.0 |
| internal_support_sources_not_expected_in_search | 1 |
| kept_figure1_rows_total | 1548 |
| kept_figure1_rows_rediscovered | 1542 |
| kept_row_recall_percent | 99.6 |
| search_manifest_records | 7214 |

## Missed External Sources

No externally searchable known-good sources were missed.

## Internal Support Sources Not Expected In Search

| Source | Kept Figure 1 Rows | Reason |
| --- | ---: | --- |
| Appendix D supplemental | 6 | internal hand-built/support artifact |

## Top Rediscovered Sources

| Source | Kept Figure 1 Rows | Match Type | Search Row |
| --- | ---: | --- | --- |
| FReD filtered pair table | 685 | url | FORRT Replication Database \| FORRT Replication Database |
| SCORE analyst join | 171 | url | Materials for "Investigating the replicability of the social and behavioral sciences" |
| LOOPR coding workbook | 104 | alias | How Replicable Are Links Between Personality Traits and Consequential Life Outcomes? The Life Outcomes of Personality Replication Project \| Systematically Testi |
| RPP canonical OSF csv | 63 | alias | What Should Researchers Expect When They Replicate Studies? A Statistical View of Replicability in Psychological Science \| Bayesian evaluation of effect size af |
| Coppock 2019 generalizability corpus | 35 | alias | coppock generalizability promoted pairs \| coppock generalizability promoted pairs \| coppock generalizability promoted pairs \| coppock generalizability promoted  |
| Boyce student replication corpus | 35 | alias | Eleven years of student replication projects provide evidence on the correlates of replicability in psychology. \| Eleven years of student replication projects p |
| RPCB | 33 | url | Replication Data from the Reproducibility Project: Cancer Biology \| Replication Data from the Reproducibility Project: Cancer Biology \| Replication Data from th |
| Kerschbaumer 2020 rheumatology phase II/III | 32 | alias | kerschbaumer 2020 rheumatology phase2 phase3 acr20 promoted pairs \| kerschbaumer 2020 rheumatology phase2 phase3 acr20 promoted pairs \| Minimizing efficacy diff |
| Communication privacy replication corpus | 31 | alias | lead registry \| lead registry \| lead registry \| lead registry \| Privacy calculus, privacy paradox, and context collapse: A replication of three key studies in c |
| Many Labs 2 public join | 28 | alias | Many Labs 2: Investigating Variation in Replicability Across Samples and Settings \| Many Labs 2: Investigating Variation in Replicability Across Samples and Set |
| EPRP complete data | 27 | alias | Replication of null results: Absence of evidence or evidence of absence? \| Replication of null results: Absence of evidence or evidence of absence? \| The assess |
| Decision-market pair table | 26 | alias | A comparison of contractors’ decision to bid behaviour according to different market environments \| Retail Location Decision Making Using a Market Potential App |
| BRI primary t experiment table | 21 | alias | Brazilian Reproducibility Initiative Survey of Beliefs Data \| Brazilian Reproducibility Initiative Analysis Data \| Brazilian Reproducibility Initiative Analysis |
| Management Science Replication Project | 20 | alias | msrp additional report tables promoted pairs \| msrp croson donohue promoted pairs \| msrp schweitzer cachon promoted pairs \| msrp additional report tables promot |
| Many Labs 5 overarching analyses | 20 | alias | Many Labs 5: Testing Pre-Data-Collection Peer Review as an Intervention to Increase Replicability \| Many Labs 5: Testing Pre-Data-Collection Peer Review as an I |
| ReplicationSuccess SSRP.rda | 18 | alias | Linguistic Compression Predicts Replication Failure \| The Sceptical Bayes Factor for the Assessment of Replication Success \| Linguistic Compression Predicts Rep |
| 251 Rescue parsed data | 17 | url | Using prediction markets to predict replication outcomes of 28 classic articles in social psychology and judgment and decision making |
| Sports science supplemental outcomes table | 16 | alias | Reflections on Conducting a Large Replication Project in Sports and Exercise Science \| Reflections on Conducting a Large Replication Project in Sports and Exerc |
| Awesome replicability-data repository | 11 | alias | awesome lie language promoted pairs \| awesome lie language promoted pairs \| awesome lie language promoted pairs \| awesome lie language promoted pairs \| this is  |
| ReplicationSuccess RProjects.rda | 11 | alias | Bayesian evaluation of effect size after replicating an original study \| Bayesian evaluation of effect size after replicating an original study \| Bayesian evalu |
| Altmejd harmonized Many Labs 1 | 10 | alias | Linguistic Compression Predicts Replication Failure \| Linguistic Compression Predicts Replication Failure |
| Altmejd harmonized Many Labs 3 | 10 | alias | Many Labs 3 Manuscript Tables \| Many Labs 3 Manuscript Tables \| Many Labs 3: Evaluating participant pool quality across the academic semester via replication \|  |
| Pipeline supplement + packet data | 10 | alias | Data from a pre-publication independent replication initiative examining ten moral judgement effects. \| Data Descriptor: Data from a pre-publication independent |
| Public-administration blame experiment replication | 9 | alias | public admin blame wiley table reconstruction promoted pairs \| public admin blame wiley table reconstruction promoted pairs |
| Clinical published replication workbook | 7 | alias | Contradictions in Highly Cited Clinical Research \| Contradictions in Highly Cited Clinical Research—Reply |
