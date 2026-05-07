# Figure 1 Individual Replication Search Help Prompt - 2026-05-05

Use this prompt with GPT, Gemini, or another research assistant when the next
goal is individual replication pairs, not more many-row corpora.

## Prompt

I am building a dataset for a figure comparing effect sizes in original studies
against larger-sample replications or follow-up studies. We have already run a
broad corpus/database search and should now move to **individual replication
papers or paper pairs**.

Please help find **specific original-vs-replication/follow-up pairs** that can
be checked from public source objects.

Definitions:

- An **original** is the earlier study, experiment, trial, claim, or focal result.
- A **replication/follow-up** is a later paper, report, trial, preprint, registered
  report, or source package that explicitly says it replicates, reproduces,
  re-tests, validates, follows up, extends, rescues, or definitively tests that
  earlier result.
- A **strict Figure 1A row** needs an original effect, original N, replication or
  follow-up effect, and replication or follow-up N, all on a D/SMD-compatible
  scale or convertible to D by standard statistic-to-D rules.
- A **Figure 1B D-equivalent row** can use comparative binary endpoints if both
  sides expose treatment/control event counts or OR/logOR/RR/RD plus the inputs
  needed for a documented conversion. One-arm ORR does not qualify for D-equivalent
  without a defensible comparator.
- A **native-only row** has paired native effects and N on both sides but cannot
  defensibly go on the D axis. Keep it separate.
- A **coverage-only lead** has a clear original/follow-up pair but public bytes
  do not expose enough effect/N values.

Current local state:

- Strict Figure 1A already has 1,679 rows.
- D-equivalent diagnostic rows are staged separately.
- Native-effect rows are staged separately.
- Many-replication corpora have mostly saturated. Do **not** return famous
  corpora unless you find a new individual paper pair or a missing source object.

Do not spend effort on:

- Generic replication databases, corpus/database suggestions, or named
  replication projects unless they reveal a specific individual pair not already
  captured.
- Same-data robustness/reanalysis only, unless it has a clear native-effect or
  D-equivalent route and you label it as reproduction/robustness rather than
  independent replication.
- One-arm response-rate results without a comparator.
- Computational reproducibility benchmark reports unless their metrics and N are
  defensibly mapped into a separate native route.
- Papers that merely say "future work should replicate this" or "this has been
  cited by later studies." I need affirmative replication/follow-up relation
  evidence.

Search strategy:

1. Search exact phrases that identify individual replication papers:
   - `"failed to replicate" "effect size" "sample size"`
   - `"direct replication" "Cohen's d" "original study"`
   - `"replication of" "original study" "sample size"`
   - `"we replicated" "sample size" "effect size"`
   - `"registered replication report" "[phenomenon]"`
   - `"high-powered replication" "original effect"`
   - `"larger sample" "replication" "original"`
   - `"follow-up study" "original effect" "sample size"`
   - `"definitive trial" "pilot trial" "effect size"`
   - `"pilot trial" "full-scale trial" "same outcome"`
   - `"external validation" "original study" "effect size"`

2. Search from known replication-heavy domains:
   - social psychology, cognitive psychology, judgment and decision making,
     marketing, management, experimental economics, political science, education,
     sports/exercise science, clinical psychology, public health, clinical trials,
     preclinical biology, animal behavior, developmental psychology.

3. For each candidate, find public source objects:
   - original paper DOI/PMID/PMCID/URL;
   - replication paper DOI/PMID/PMCID/URL;
   - supplement, OSF/Dataverse/GitHub/Zenodo/Figshare/Dryad package, or PMC full text;
   - tables/figures that expose effect, N, CI, p, t/F/r/OR/RR/HR, means/SDs, or event counts.

4. Prefer pairs where the replication/follow-up N is larger than the original N.
   If not larger, still record it as `strict_dn_blocked_by_current_rule`.

For each candidate, output JSON only, using this schema:

```json
{
  "task_id": "individual_replication_search",
  "candidates": [
    {
      "candidate_id": "short_slug",
      "candidate_name": "Original phenomenon or paper -> replication paper",
      "domain": "field/domain",
      "candidate_route": "strict_figure1a | d_equivalent_figure1b | native_only | coverage_only | reject",
      "confidence": "high | medium | low",
      "original": {
        "title": "",
        "authors_year": "",
        "doi": "",
        "pmid": "",
        "pmcid": "",
        "url": "",
        "source_object_urls": [],
        "effect_text_or_table_hint": "",
        "n_text_or_table_hint": ""
      },
      "replication_or_followup": {
        "title": "",
        "authors_year": "",
        "doi": "",
        "pmid": "",
        "pmcid": "",
        "url": "",
        "source_object_urls": [],
        "effect_text_or_table_hint": "",
        "n_text_or_table_hint": ""
      },
      "relationship_evidence": {
        "replication_kind": "direct_replication | conceptual_replication | followup_larger_trial | validation | reproduction_same_data | other",
        "verbatim_or_paraphrased_basis": "",
        "where_seen": "abstract | introduction | methods | table | supplement | data package | other"
      },
      "value_availability": {
        "has_original_effect": "yes | no | unclear",
        "has_replication_or_followup_effect": "yes | no | unclear",
        "has_original_n": "yes | no | unclear",
        "has_replication_or_followup_n": "yes | no | unclear",
        "effect_metric": "d | g | r | t | F | chi_square | OR | RR | RD | HR | mean_sd | event_counts | proportion | native_other | unclear",
        "conversion_route": "direct_d | statistic_to_d | logOR_to_d_equivalent | baseline_aware_binary_to_d_equivalent | native_only | none",
        "replication_n_larger_than_original_n": "yes | no | unclear"
      },
      "source_objects_to_mirror_first": [
        {
          "url": "",
          "object_type": "pdf | html | pmc_xml | supplement | data_package | code | table | registry | other",
          "why_needed": ""
        }
      ],
      "dedupe_risk": "low | medium | high",
      "possible_existing_source_family_overlap": "",
      "likely_row_count": 1,
      "blockers_or_cautions": [],
      "recommended_next_action": "mirror_source_objects | parse_public_tables | manual_pdf_extraction | request_only_no_go | reject"
    }
  ],
  "searches_run": [
    {
      "query_or_route": "",
      "source": "Google Scholar | PubMed | EuropePMC | Crossref | OpenAlex | OSF | Dataverse | GitHub | citation_snowball | other",
      "useful_hits": 0,
      "notes": ""
    }
  ],
  "high_confidence_rejections": [
    {
      "name": "",
      "reason": "same_data_only | no_original_mapping | no_effect_or_n | one_arm_no_comparator | corpus_already_covered | not_a_replication | other",
      "url": ""
    }
  ]
}
```

Rules:

- Give direct URLs wherever possible.
- Do not infer effect/N values from prose unless the source explicitly gives
  them or gives enough table fields to compute them.
- Do not rely on a citation count or later related paper as replication evidence.
- If source objects are paywalled, bot-blocked, or request-only, say so and do
  not pretend the row is usable.
- If a candidate looks already captured by a famous corpus, still return it only
  if you can name the likely overlap so we can dedupe it.
- Favor 10-30 high-quality candidates over a large noisy list.

The most useful output is a list of specific mirrorable source objects that can
be turned into one-row extraction tasks.

## How This Enters The YAML Strategy

This prompt belongs under `search_plan_plot1_replication_pairs`, not under the
corpus/database plan. Its output should be saved as an individual-search target
manifest, for example:

```text
steps/searches/figure1/individualrepsearch-gpt-batch001.json
```

The manifest should feed an individual-paper worklist, not
`CORPORA_AND_DATABASES.tsv`, unless the answer unexpectedly identifies a true
multi-row source family.

Recommended route mapping:

- `strict_figure1a` -> individual source-object acquisition and D/N extraction.
- `d_equivalent_figure1b` -> Figure 1B clinical/binary diagnostic worklist.
- `native_only` -> native-effect retention worklist.
- `coverage_only` -> source-object denominator, no quantitative row yet.
- `reject` -> keep in rejected/context ledger with reason.
