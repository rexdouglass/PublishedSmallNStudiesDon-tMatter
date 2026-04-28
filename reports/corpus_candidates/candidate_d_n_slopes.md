# Candidate D-vs-N Slopes

Log-log model: `log10(D) ~ log10(N)`. Slopes near -0.5 are the boundary-hugging pattern from the current paper figure.

## Published Original Candidates, Paper Level

| source_corpus                                  | field                                       |    n |   slope |   slope_se |   r_squared |   median_D |     median_N |
|:-----------------------------------------------|:--------------------------------------------|-----:|--------:|-----------:|------------:|-----------:|-------------:|
| rpcb_cancer_biology                            | preclinical_cancer_biology                  |   20 | -0.8168 |    0.1754  |     0.5463  |    2.281   |   11.25      |
| havranek_gasoline_income                       | economics                                   |   50 | -0.7511 |    0.1096  |     0.4946  |    2.849   |   18         |
| havranek_armington                             | economics                                   |   24 | -0.6643 |    0.1303  |     0.5417  |    1.337   |   20.5       |
| forrt_fred                                     | Judgment and Decision Making                |   25 | -0.6433 |    0.1615  |     0.4082  |    0.547   |  152         |
| forrt_fred                                     | Economics                                   |   28 | -0.5603 |    0.1059  |     0.5185  |    0.4646  |  122         |
| forrt_fred                                     | Marketing                                   |   35 | -0.5384 |    0.09259 |     0.5061  |    0.4144  |  171         |
| forrt_fred                                     | Psychology                                  |   55 | -0.5375 |    0.0916  |     0.3938  |    0.5927  |   91         |
| havranek_eis                                   | economics                                   |   33 | -0.5096 |    0.06582 |     0.6592  |    0.239   |  239         |
| havranek_substitution                          | economics                                   |   33 | -0.5096 |    0.06582 |     0.6592  |    0.239   |  239         |
| forrt_fred                                     | Developmental Psychology                    |   12 | -0.5092 |    0.1835  |     0.435   |    0.8748  |   36.5       |
| clinifact_published_primary_pairs              | medicine_rct                                |  339 | -0.5049 |    0.03716 |     0.3539  |    0.3307  |  215         |
| score_cos_claims                               | economics and finance                       |  193 | -0.4872 |    0.01327 |     0.8759  |    0.2174  |  599         |
| forrt_fred                                     | Differential Psychology                     |   23 | -0.4647 |    0.05852 |     0.7502  |    0.3427  |  226         |
| dellavigna_linos_2022                          | economics_nudge                             |   27 | -0.4631 |    0.07976 |     0.5741  |    0.1411  | 1146         |
| forrt_fred                                     | Social Psychology                           |  241 | -0.4614 |    0.03558 |     0.413   |    0.6017  |   96         |
| score_cos_claims                               | political science                           |  411 | -0.4581 |    0.01225 |     0.7738  |    0.1896  |  718         |
| forrt_fred                                     | psychology                                  |   27 | -0.4536 |    0.05276 |     0.7472  |    0.5975  |   85         |
| olsson_sundell_2023_social_interventions       | social_intervention_research                |  250 | -0.4521 |    0.07544 |     0.1265  |    0.4305  |   89         |
| replication_pair_originals_bridge              | sports science                              |   15 | -0.4496 |    0.5216  |     0.05406 |    1.247   |   14         |
| score_cos_claims                               | business                                    |  603 | -0.4466 |    0.01106 |     0.7308  |    0.2931  |  265         |
| forrt_fred                                     | political science                           |   10 | -0.428  |    0.06843 |     0.8302  |    0.3053  | 2076         |
| score_cos_claims                               | education                                   |  373 | -0.4244 |    0.01436 |     0.7018  |    0.3931  |  212         |
| score_cos_claims                               | education                                   |   17 | -0.4232 |    0.08978 |     0.597   |    0.198   | 2835         |
| havranek_frisch_extensive                      | economics                                   |   16 | -0.4177 |    0.1523  |     0.3495  |    0.1586  |    1.367e+04 |
| economics_brodeur_2024                         | economics                                   |  217 | -0.4177 |    0.0192  |     0.6876  |    0.07144 | 2000         |
| forrt_fred                                     | economics                                   |   12 | -0.4164 |    0.07482 |     0.7559  |    0.3969  |  237         |
| esarey_wu_2016_political_science_main_findings | political_science                           |  167 | -0.4132 |    0.02437 |     0.6353  |    0.2333  |  722         |
| score_cos_claims                               | sociology and criminology                   |  458 | -0.4042 |    0.01578 |     0.5901  |    0.1537  | 1977         |
| score_cos_claims                               | economics and finance                       |   48 | -0.4012 |    0.04656 |     0.6174  |    0.3952  |  343         |
| button_nord_neuroscience                       | neuroscience                                |  649 | -0.3815 |    0.02619 |     0.247   |    0.2126  |  107         |
| kuhberger_2014_main_results                    | psychology                                  |  472 | -0.3815 |    0.02712 |     0.2963  |    0.7229  |   94         |
| score_cos_claims                               | psychology and health                       |  855 | -0.3534 |    0.01203 |     0.5028  |    0.46    |  183         |
| replication_pair_originals_bridge              | political science / economics               |   37 | -0.3523 |    0.09691 |     0.2741  |    0.3347  |  323         |
| score_cos_claims                               | business                                    |   43 | -0.3405 |    0.06888 |     0.3735  |    0.4448  |  173         |
| forrt_fred                                     | Education                                   |   13 | -0.3401 |    0.1158  |     0.4394  |    0.4987  |  137         |
| replication_pair_originals_bridge              | medicine                                    |   56 | -0.339  |    0.06232 |     0.354   |    0.7467  |  103.5       |
| yun_llm_meta_analysis                          | medicine_rct                                |   85 | -0.3263 |    0.09989 |     0.1139  |    0.2895  |   77         |
| replication_pair_originals_bridge              | experimental philosophy                     |   29 | -0.3255 |    0.1354  |     0.1764  |    0.6755  |   78         |
| metalab                                        | developmental_psychology                    |  188 | -0.3249 |    0.1428  |     0.02707 |    0.5325  |   20         |
| score_cos_claims                               | psychology and health                       |  116 | -0.3212 |    0.04003 |     0.3609  |    0.5746  |  222.5       |
| linden_2024_focal_effects                      | psychology                                  |  158 | -0.3203 |    0.04456 |     0.2488  |    0.63    |   83.5       |
| forrt_fred                                     | Cognitive Psychology                        |  163 | -0.3196 |    0.04569 |     0.2331  |    0.8069  |   40         |
| schaefer_schwarz_2019_without_prereg           | psychology                                  |  682 | -0.3163 |    0.02274 |     0.2215  |    0.7717  |   68.5       |
| motyl_2017_critical_tests                      | psychology_social_personality               |  540 | -0.3004 |    0.02145 |     0.2672  |    0.6142  |   93.75      |
| schaefer_schwarz_2019_with_prereg              | psychology                                  |   89 | -0.2873 |    0.08464 |     0.1169  |    0.3268  |  268         |
| forrt_fred                                     | Neuroscience                                |   11 | -0.2517 |    0.1246  |     0.312   |    0.7544  |   42         |
| forrt_fred                                     | marketing/org behavior                      |   17 | -0.2464 |    0.1258  |     0.2035  |    0.5004  |  106         |
| forrt_fred                                     | Political Psychology                        |   10 | -0.2256 |    0.2857  |     0.07233 |    0.4948  |  201         |
| score_cos_claims                               | sociology and criminology                   |   31 | -0.2213 |    0.08058 |     0.2064  |    0.1152  | 1921         |
| replication_pair_originals_bridge              | psychology and adjacent replication targets |  284 | -0.217  |    0.0348  |     0.1212  |    0.6454  |   79.5       |
| forrt_fred                                     | Experimental Philosophy                     |   40 | -0.1798 |    0.07638 |     0.1273  |    0.6068  |   93.5       |
| dellavigna_linos_2022                          | economics_nudge                             |   16 | -0.1702 |    0.1157  |     0.1338  |    0.03035 |    1.066e+04 |
| score_cos_claims                               | political science                           |   45 | -0.1386 |    0.06361 |     0.09937 |    0.3162  |  798         |
| metabus_open_bosco                             | io_psychology_management                    | 1999 | -0.1206 |    0.01121 |     0.0548  |    0.3765  |  181         |
| turner_antidepressants_2022                    | medicine_psychiatry                         |   23 |  0.2654 |    0.5427  |     0.01126 |    0.2714  |  383.5       |
| forrt_fred                                     | Linguistics                                 |   11 |  0.3917 |    0.6541  |     0.03831 |    0.77    |   51         |

## Notes

- Paper-level slopes are more comparable to the current statcheck/economics figure.
- Row-level slopes are also written to CSV, but they overweight many-test papers and dense catalogs.
- Szucs is absent from paper-level results until its MATLAB journal/paper grouping is decoded.
