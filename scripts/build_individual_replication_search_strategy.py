#!/usr/bin/env python3
"""Materialize the Figure 1 individual-replication search strategy."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "steps" / "searches" / "figure1"
PROMPT = ROOT / "reports" / "figure1_individual_replication_search_help_prompt_2026-05-05.md"
VAST_PROMPT = ROOT / "reports" / "figure1_individual_replication_vast_search_prompt_2026-05-05.md"
STRATEGY_TSV = OUT_DIR / "individualrepsearch-tool-strategy.tsv"
SCHEMA_JSON = OUT_DIR / "individualrepsearch-candidate-schema.json"
README_MD = OUT_DIR / "individualrepsearch-intake-readme.md"
VAST_QUERY_TSV = OUT_DIR / "individualrepsearch-vast-query-bank.tsv"
VAST_RUN_PLAN_MD = OUT_DIR / "individualrepsearch-vast-run-plan.md"
RECALL_PROBES_TSV = OUT_DIR / "individualrepsearch-known-good-recall-probes.tsv"
RELATION_EVIDENCE_TSV = OUT_DIR / "individualrepsearch-relation-evidence-scale.tsv"
ROUTING_SCORE_TSV = OUT_DIR / "individualrepsearch-routing-score-rules.tsv"
QUERY_LOG_SCHEMA_TSV = OUT_DIR / "individualrepsearch-query-log-schema.tsv"
DESIGN_YML = OUT_DIR / "individualrepsearch-design.yml"


TRACKS = [
    {
        "track_id": "gpt_or_gemini_assisted_pair_search",
        "tool_or_surface": "GPT/Gemini/deep research",
        "query_or_prompt": str(PROMPT.relative_to(ROOT)),
        "target_manifest": "steps/searches/figure1/individualrepsearch-gpt-<batch>.json",
        "accept_if": "specific original-vs-replication/follow-up pair with affirmative relation evidence and source-object URLs",
        "reject_if": "corpus-only suggestion, related citation without replication assertion, one-arm no-comparator, or same-data robustness without explicit route",
        "next_step": "figure1-individual-replication-search-intake",
    },
    {
        "track_id": "bibliographic_phrase_search",
        "tool_or_surface": "Crossref/OpenAlex/PubMed/EuropePMC/paperclip",
        "query_or_prompt": '"failed to replicate" "original study"; "direct replication" "sample size"; "registered replication report"',
        "target_manifest": "steps/searches/figure1/individualrepsearch-bibliographic-<query>.json",
        "accept_if": "bibliographic record is an individual replication/follow-up paper and names the original or target claim",
        "reject_if": "review/editorial/meta-analysis-only record or no original target",
        "next_step": "figure1-individual-replication-search-intake",
    },
    {
        "track_id": "repository_package_search",
        "tool_or_surface": "OSF/Dataverse/Zenodo/Figshare/Dryad/GitHub",
        "query_or_prompt": '"direct replication" "original study" data; "replication package" "original effect"',
        "target_manifest": "steps/searches/figure1/individualrepsearch-repository-<surface>.json",
        "accept_if": "one-paper package with source objects, data, code, or tables that identify original and replication sides",
        "reject_if": "multi-row corpus already routed elsewhere or materials-only package with no result route",
        "next_step": "figure1-individual-replication-search-intake",
    },
    {
        "track_id": "known_original_forward_search",
        "tool_or_surface": "OpenAlex/Semantic Scholar/Crossref/manual citation snowball",
        "query_or_prompt": "cited-by around famous original effects; filter for replicate/reproduce/validate/follow-up/high-powered",
        "target_manifest": "steps/searches/figure1/individualrepsearch-citation-<batch>.json",
        "accept_if": "citing paper self-describes replication/validation/follow-up and can ground both source identities",
        "reject_if": "mere citation, theory extension, or no result-level source-object route",
        "next_step": "figure1-individual-replication-search-intake",
    },
    {
        "track_id": "clinical_pair_rescue_search",
        "tool_or_surface": "PubMed/EuropePMC/paperclip/ClinicalTrials.gov/Crossref/OpenAlex",
        "query_or_prompt": '"pilot trial" "full-scale trial"; "phase II" "phase III" "same endpoint"; "definitive trial"',
        "target_manifest": "steps/searches/figure1/individualrepsearch-clinical-<batch>.json",
        "accept_if": "same/close clinical endpoint and public source object exposes comparative effect/N or D-equivalent inputs",
        "reject_if": "ordinary development sequence with no replication/follow-up assertion or one-arm ORR without comparator",
        "next_step": "figure1-individual-replication-search-intake",
    },
    {
        "track_id": "direct_replication_language_sweep",
        "tool_or_surface": "web/PubMed/PMC/Crossref/OpenAlex/Semantic Scholar",
        "query_or_prompt": '"direct replication of"; "failed to replicate"; "failure to replicate"; "first direct replication"; "two failures to replicate"; "three unsuccessful attempts to replicate"; "pre-registered replication"; "high-powered direct replication"; "using the original materials and methods"',
        "target_manifest": "steps/searches/figure1/individualrepsearch-direct-language-<batch>.json",
        "accept_if": "paper-level hit names the original target paper/effect and provides a source-object route for both sides or a replication paper that quotes original values",
        "reject_if": "review-only, same-data reanalysis, commentary, or generic replication discussion without a target pair",
        "next_step": "figure1-individual-replication-search-intake",
    },
    {
        "track_id": "value_language_sweep",
        "tool_or_surface": "web/PMC/PLOS/open publisher HTML/full text search",
        "query_or_prompt": '"Cohen\'s d" "original study" "replication study" "N ="; "effect size" "replication" "original" "sample size"; "means and standard deviations" "direct replication" "original"; "forest plot" "original study" "replication"',
        "target_manifest": "steps/searches/figure1/individualrepsearch-value-language-<batch>.json",
        "accept_if": "hit likely contains original and replication value text or table values, even if it is not yet deduped",
        "reject_if": "value language is only in a broad meta-analysis without individual source identities",
        "next_step": "figure1-individual-replication-search-intake",
    },
    {
        "track_id": "plos_and_open_journal_replication_sweep",
        "tool_or_surface": "PLOS ONE/PMC/open journal HTML",
        "query_or_prompt": 'site:journals.plos.org/plosone "Direct replication of"; site:journals.plos.org/plosone "Failed replication"; site:journals.plos.org/plosone "failure to replicate"; site:pmc.ncbi.nlm.nih.gov "direct replication" "Cohen\'s d" "original"',
        "target_manifest": "steps/searches/figure1/individualrepsearch-open-journals-<batch>.json",
        "accept_if": "open full text has a paper-level replication relation and likely extractable effect/N or raw data links",
        "reject_if": "method paper, editorial, or same-data reproducibility-only article",
        "next_step": "figure1-individual-replication-search-intake",
    },
    {
        "track_id": "behavioral_economics_marketing_replication_sweep",
        "tool_or_surface": "web/Crossref/OpenAlex/OSF/Dataverse",
        "query_or_prompt": '"failed to replicate" "consumer behavior" "direct replication"; "replication" "behavioral economics" "original study" "Cohen\'s d"; "marketing" "direct replication" "Cohen\'s d"; "management" "failed to replicate" "original study"',
        "target_manifest": "steps/searches/figure1/individualrepsearch-behavioral-econ-marketing-<batch>.json",
        "accept_if": "one-off marketing, management, behavioral-economics, or consumer-behavior replication pair with extractable values or a repository package",
        "reject_if": "registered report/project already represented as a many-row source family unless a specific missing paper pair is identified",
        "next_step": "figure1-individual-replication-search-intake",
    },
    {
        "track_id": "clinical_trial_reversal_followup_sweep",
        "tool_or_surface": "PubMed/PMC/paperclip/ClinicalTrials.gov/NEJM/JAMA/BMJ",
        "query_or_prompt": '"single-center" "multicenter" "{intervention}" mortality "trial"; "landmark trial" "{intervention}" "subsequent trial"; "failed to confirm" "{intervention}" "randomized trial"; "larger trial" "{intervention}" "no benefit" "mortality"; "trial reversal" "{intervention}" "original trial"',
        "target_manifest": "steps/searches/figure1/individualrepsearch-clinical-reversal-<batch>.json",
        "accept_if": "original and follow-up trials have the same/close comparative endpoint with event counts or OR/RR/RD inputs for D-equivalent routing",
        "reject_if": "ordinary development sequence, different endpoint/population without explicit replication/follow-up framing, or one-arm ORR without comparator",
        "next_step": "figure1-individual-replication-search-intake",
    },
    {
        "track_id": "genetics_validation_sweep",
        "tool_or_surface": "PubMed/PMC/GWAS Catalog/Crossref/OpenAlex",
        "query_or_prompt": '"failed to replicate" "{gene}" "{phenotype}" "{original_author}"; "independent validation" "{gene}" "{phenotype}" "odds ratio" "sample size"; "collaborative meta-analysis" "{gene}" "{phenotype}" "no evidence"; "candidate gene" "failed to replicate" "{phenotype}"',
        "target_manifest": "steps/searches/figure1/individualrepsearch-genetics-validation-<batch>.json",
        "accept_if": "explicit discovery-vs-independent-validation or original-vs-large-follow-up pair with effect/N fields or native interaction estimates",
        "reject_if": "meta-analysis-only without target source identity or no pairable original claim",
        "next_step": "figure1-individual-replication-search-intake",
    },
    {
        "track_id": "education_health_sports_replication_sweep",
        "tool_or_surface": "web/PubMed/PMC/Crossref/OpenAlex/OSF",
        "query_or_prompt": '"three failures to replicate" "growth mindset"; "active-control" "replication" "{education_intervention}"; "replication study" "time-to-exhaustion" "mental fatigue"; "failed to replicate" "exercise science" "Cohen\'s d"; "health behavior" "direct replication" "original study"',
        "target_manifest": "steps/searches/figure1/individualrepsearch-education-health-sports-<batch>.json",
        "accept_if": "education, health behavior, or sport/exercise one-off replication with a specific original target and effect/N route",
        "reject_if": "implementation/scale-up without original mapping or no comparable endpoint",
        "next_step": "figure1-individual-replication-search-intake",
    },
    {
        "track_id": "negative_filter_same_data_and_computational_only",
        "tool_or_surface": "all search surfaces",
        "query_or_prompt": '"multiverse analysis"; "reanalysis"; "same data"; "robustness check"; "analyst variability"; "reproduced the code"; "same dataset" "replication"',
        "target_manifest": "steps/searches/figure1/individualrepsearch-context-negative-<batch>.json",
        "accept_if": "only as context/explicit exclusion unless a separate computational/native subplot route is intentionally opened",
        "reject_if": "candidate is being proposed for strict Figure 1A without new data or a new independent follow-up sample",
        "next_step": "figure1-individual-replication-search-intake",
    },
]


def slugify(text: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in text.lower()).strip("_")


def build_query_bank() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    def add(
        *,
        campaign_phase: str,
        surface: str,
        query_type: str,
        route_bias: str,
        priority: int,
        queries: list[str],
        expected_signal: str,
        reject_signal: str = "same-data reanalysis, review-only article, no original target, or no new independent sample",
    ) -> None:
        for query in queries:
            query_id = f"{slugify(f'{campaign_phase}_{surface}_{query}')[:72]}_{len(rows) + 1:04d}"
            rows.append(
                {
                    "campaign_phase": campaign_phase,
                    "surface": surface,
                    "query_type": query_type,
                    "priority": str(priority),
                    "query_id": query_id,
                    "query": query,
                    "candidate_route_bias": route_bias,
                    "expected_signal": expected_signal,
                    "reject_signal": reject_signal,
                    "dedupe_gate": "original DOI/title + replication DOI/title + outcome/study key; then figure1-pair-bibtex-map.tsv",
                    "target_manifest": f"steps/searches/figure1/individualrepsearch-{slugify(surface)}-{query_id}.json",
                    "next_step": "figure1-individual-replication-search-intake",
                }
            )

    add(
        campaign_phase="01_metadata_replication_language",
        surface="OpenAlex/Crossref/SemanticScholar",
        query_type="title_abstract_metadata",
        route_bias="strict_figure1a",
        priority=1,
        queries=[
            '"direct replication of" "Cohen\'s d"',
            '"failed to replicate" "Cohen\'s d" "original study"',
            '"failure to replicate" "effect size" "sample size"',
            '"first direct replication" "effect size"',
            '"high-powered replication" "original effect"',
            '"pre-registered replication" "original effect"',
            '"registered replication report" "original study"',
            '"two failures to replicate" "original"',
            '"three unsuccessful attempts to replicate" "original"',
            '"we attempted to replicate" "effect size" "original"',
            '"has not been replicated directly" "we report"',
            '"not been directly replicated" "original study"',
            '"Study 1 from" "direct replication"',
            '"same materials" "larger sample" "failed to replicate"',
            '"using the original materials and methods" "replicate"',
        ],
        expected_signal="paper title/abstract explicitly says it replicated an earlier paper/effect and likely reports D/statistic/N",
    )
    add(
        campaign_phase="02_open_full_text_value_language",
        surface="PMC/PLOS/EuropePMC full text",
        query_type="full_text",
        route_bias="strict_figure1a",
        priority=1,
        queries=[
            '"direct replication" "Cohen\'s d" "original study" "N ="',
            '"effect size" "replication" "original" "sample size"',
            '"means and standard deviations" "direct replication" "original"',
            '"forest plot" "original study" "replication" "Cohen\'s d"',
            '"original effect size" "replication effect size" "sample size"',
            '"original study" "replication study" "d ="',
            '"we replicated" "original" "Cohen\'s d" "participants"',
            '"larger sample" "failed to replicate" "Cohen\'s d"',
            '"event counts" "original" "replication" "odds ratio"',
            '"2x2" "replication" "sample size" "original"',
            '"Table 1" "original" "replication" "Cohen\'s d"',
            '"sample size" "original" "replication" "validation cohort"',
        ],
        expected_signal="open full text likely has value-bearing prose, tables, or figure captions for both sides",
    )
    add(
        campaign_phase="03_repository_source_object_search",
        surface="OSF/Figshare/Dataverse/Zenodo/GitHub",
        query_type="repository_package",
        route_bias="strict_figure1a",
        priority=2,
        queries=[
            '"direct replication" "data" "Cohen"',
            '"failed replication" "data" "original"',
            '"registered replication report" "data"',
            '"replication package" "original" "replication"',
            '"original_effect" "replication_effect"',
            '"original_N" "replication_N"',
            '"replication study" "means" "standard deviations"',
            '"replication" "effect_size" "sample_size"',
            '"original study" "replication study" "csv"',
            '"direct replication" "analysis script"',
        ],
        expected_signal="repository record or code/data package supports one paper pair or one replication report with extractable values",
        reject_signal="materials-only repository, many-row corpus already routed, or package without original target/result mapping",
    )
    add(
        campaign_phase="04_psychology_long_tail",
        surface="OpenAlex/Crossref/PubMed/web",
        query_type="domain_phrase",
        route_bias="strict_figure1a",
        priority=2,
        queries=[
            '"behavioral priming" "failed to replicate" "Cohen\'s d"',
            '"social priming" "direct replication" "original"',
            '"embodied cognition" "failed to replicate" "Cohen\'s d"',
            '"moral psychology" "direct replication" "effect size"',
            '"judgment and decision making" "failed to replicate" "Cohen\'s d"',
            '"cognitive psychology" "direct replication" "sample size"',
            '"developmental psychology" "multilab direct replication"',
            '"psychology of religion" "direct replication" "Cohen\'s d"',
            '"social neuroscience" "failed replication" "effect size"',
        ],
        expected_signal="one-off psychology replication not already captured by RPP/Many Labs/RRR source families",
    )
    add(
        campaign_phase="05_behavioral_econ_marketing_management",
        surface="OpenAlex/Crossref/OSF/Dataverse/web",
        query_type="domain_phrase",
        route_bias="strict_figure1a",
        priority=2,
        queries=[
            '"failed to replicate" "consumer behavior" "direct replication"',
            '"marketing" "direct replication" "Cohen\'s d"',
            '"management" "failed to replicate" "original study"',
            '"behavioral economics" "direct replication" "sample size"',
            '"dishonesty" "registered replication report" "effect size"',
            '"risk taking" "replication" "Cohen\'s d" "original"',
            '"mating motives" "replication" "consumer"',
            '"prosocial behavior" "direct replication" "original effect"',
        ],
        expected_signal="one-off behavioral-econ/marketing/management replication with effect/N or data package",
    )
    add(
        campaign_phase="06_education_health_sports",
        surface="PubMed/PMC/OpenAlex/Crossref/web",
        query_type="domain_phrase",
        route_bias="strict_figure1a",
        priority=3,
        queries=[
            '"growth mindset" "failed to replicate" "effect size"',
            '"active-control" "replication" "growth mindset"',
            '"education" "direct replication" "Cohen\'s d"',
            '"health behavior" "direct replication" "original study"',
            '"exercise science" "failed to replicate" "Cohen\'s d"',
            '"mental fatigue" "replication study" "time-to-exhaustion"',
            '"sports psychology" "direct replication" "effect size"',
            '"public health" "larger sample" "failed to replicate" "effect size"',
        ],
        expected_signal="education/health/sport replication with comparable endpoint and D/statistic route",
    )
    add(
        campaign_phase="07_clinical_d_equivalent_followup",
        surface="PubMed/PMC/ClinicalTrials.gov/Crossref",
        query_type="clinical_trial_followup",
        route_bias="d_equivalent_figure1b",
        priority=3,
        queries=[
            '"single-center" "multicenter" "failed to confirm" "randomized trial"',
            '"landmark trial" "subsequent trial" "no benefit"',
            '"pilot trial" "definitive trial" "same outcome"',
            '"phase II" "phase III" "failed to confirm"',
            '"trial reversal" "original trial" "mortality"',
            '"larger trial" "no benefit" "mortality" "original"',
            '"randomized trial" "replication" "event counts"',
            '"external validation" "original trial" "odds ratio"',
            '"failed to confirm" "earlier trial" "mortality"',
            '"did not confirm" "single-center" "multicenter randomized trial"',
            '"confirmatory trial" "previous trial" "primary outcome"',
            '"large international randomized trial" "failed to confirm"',
        ],
        expected_signal="original and follow-up comparative trials with event counts, OR/RR/RD, N, and similar endpoint",
        reject_signal="one-arm ORR/no comparator, changed endpoint without relation evidence, or ordinary development sequence",
    )
    add(
        campaign_phase="08_genetics_validation_native",
        surface="PubMed/PMC/GWASCatalog/OpenAlex",
        query_type="genetics_validation",
        route_bias="native_only",
        priority=4,
        queries=[
            '"failed to replicate" "candidate gene" "odds ratio"',
            '"independent validation" "candidate gene" "sample size"',
            '"collaborative meta-analysis" "no evidence" "gene" "depression"',
            '"genome-wide" "failed to replicate" "original study"',
            '"polygenic" "replication" "original" "effect size"',
            '"gene by environment" "failed to replicate" "sample size"',
            '"replication cohort" "discovery cohort" "odds ratio"',
            '"validation cohort" "discovery cohort" "sample size"',
            '"independent cohort" "genetic association" "failed to replicate"',
        ],
        expected_signal="original discovery/claim and independent validation/follow-up with native model effect or OR/beta/N",
        reject_signal="meta-analysis-only with no target source identity or no pairable original claim",
    )
    add(
        campaign_phase="09_citation_snowball_known_originals",
        surface="OpenAlex/SemanticScholar/Crossref cited-by",
        query_type="citation_forward_filter",
        route_bias="coverage_only",
        priority=2,
        queries=[
            'cited-by("{original DOI}") filter title/abstract: replicate OR replication OR failed OR high-powered OR registered',
            'cited-by("{original DOI}") filter title/abstract: "no evidence" OR "failed to confirm" OR "direct replication"',
            'cited-by("{original title}") filter full text: "we replicated" OR "using the original materials"',
            'references("{replication DOI}") extract target original references and source-object URLs',
        ],
        expected_signal="citing paper names the original target and self-describes replication/follow-up; route after dedupe",
        reject_signal="ordinary citation, theory extension, or no explicit relation evidence",
    )
    add(
        campaign_phase="10_negative_filters_context",
        surface="all surfaces",
        query_type="negative_filter",
        route_bias="reject",
        priority=9,
        queries=[
            '"multiverse analysis" "{original_title}"',
            '"reanalysis" "{original_title}" "same data"',
            '"robustness check" "{original_title}"',
            '"analyst variability" "{original_title}"',
            '"reproduced the code" "{original_title}"',
            '"same dataset" "replication" "{model_name}"',
        ],
        expected_signal="keep as context/exclusion unless a separate native/computational route is explicitly opened",
        reject_signal="new Figure 1A row without independent replication/follow-up sample",
    )
    return rows


def build_recall_probes() -> list[dict[str, str]]:
    probes = [
        ("facial_feedback_strack_wagenmakers", "Strack Martin Stepper 1988", "Registered Replication Report Strack Martin Stepper", "strict_figure1a"),
        ("verbal_overshadowing_schooler_alogna", "Schooler Engstler-Schooler verbal overshadowing", "Registered Replication Report Schooler", "d_equivalent_figure1b"),
        ("ego_depletion_hagger", "Sripada Kessler Jonides ego depletion", "Multilab Preregistered Replication Ego-Depletion", "strict_figure1a"),
        ("power_posing_ranehill", "Carney Cuddy Yap power posing", "Assessing the Robustness of Power Posing", "strict_figure1a"),
        ("goal_priming_harris", "Bargh automated will goal priming", "Goal Priming and the Remoteness of Goals", "strict_figure1a"),
        ("physical_warmth_chabris", "Williams Bargh physical warmth", "No Evidence That Experiencing Physical Warmth Promotes Interpersonal Warmth", "strict_figure1a"),
        ("physical_warmth_lynott", "Williams Bargh Experiencing Physical Warmth Promotes Interpersonal Warmth", "Replication of Experiencing Physical Warmth Promotes Interpersonal Warmth Lynott", "d_equivalent_figure1b"),
        ("elderly_walking_doyen", "Bargh Chen Burrows automaticity social behavior elderly walking", "Behavioral Priming Its All in the Mind Whose Mind", "strict_figure1a"),
        ("bem_ritchie", "Bem Feeling the Future Experiment 9", "Failing the Future three unsuccessful attempts", "strict_figure1a"),
        ("analytic_religion_sanchez", "Gervais Norenzayan analytic thinking religious disbelief", "Direct Replication no evidence analytic thinking decreases religious belief", "strict_figure1a"),
        ("power_motor_cusack", "Burgmer Englich Bullseye power motor performance", "Power May Have Little to No Effect on Motor Performance", "strict_figure1a"),
        ("organic_food_moery", "Eskine organic foods moral judgments", "Organic Food Exposure Has Little to No Effect", "strict_figure1a"),
        ("social_distance_pashler", "Williams Bargh keeping one's distance", "Priming of Social Distance Failure to Replicate", "strict_figure1a"),
        ("macbeth_earp", "Zhong Liljenquist washing away sins", "Out Damned Spot Macbeth Effect", "strict_figure1a"),
        ("signing_kristal", "Shu Mazar Gino Ariely signing at beginning", "Signing at the Beginning Versus at the End Does Not Decrease Dishonesty", "d_equivalent_figure1b"),
        ("egdt_rivers_process", "Rivers early goal-directed therapy severe sepsis", "ProCESS ARISE ProMISe early septic shock", "d_equivalent_figure1b"),
        ("nice_sugar", "van den Berghe intensive insulin therapy critically ill", "NICE-SUGAR intensive versus conventional glucose control", "d_equivalent_figure1b"),
        ("marshmallow_watts", "Shoda Mischel Peake preschool delay gratification", "Revisiting the Marshmallow Test Watts Duncan Quan", "native_only"),
        ("five_httlpr_culverhouse", "Caspi 5-HTTLPR life stress depression", "Culverhouse collaborative meta-analysis no evidence strong interaction", "native_only"),
    ]
    return [
        {
            "probe_id": probe_id,
            "original_search_terms": original,
            "replication_search_terms": replication,
            "expected_route": route,
            "passes_if": "at least one query family returns the replication paper and relationship evidence before manual seeding",
            "use_for": "recall calibration before trusting long-tail search yield",
        }
        for probe_id, original, replication, route in probes
    ]


def build_relation_evidence_scale() -> list[dict[str, str]]:
    return [
        {
            "strength": "5",
            "evidence_type": "title_exact_replication",
            "accepted_when": "title names the earlier paper/authors/result and says replication, direct replication, failed replication, or equivalent",
            "example_pattern": "Replication of [original title] by [original authors]",
            "routing_use": "sufficient relation evidence for pair candidate after identity normalization",
        },
        {
            "strength": "5",
            "evidence_type": "title_registered_replication_report",
            "accepted_when": "title or metadata says Registered Replication Report and names the original authors/year/study",
            "example_pattern": "Registered Replication Report: Author and Author (year)",
            "routing_use": "sufficient relation evidence for pair candidate; still requires study/outcome grain",
        },
        {
            "strength": "4",
            "evidence_type": "abstract_direct_replication",
            "accepted_when": "abstract states that the paper replicated, retested, or attempted to replicate a named earlier study/result",
            "example_pattern": "we directly replicated Study 1 from Author et al.",
            "routing_use": "sufficient relation evidence for pair candidate",
        },
        {
            "strength": "4",
            "evidence_type": "abstract_failed_replication",
            "accepted_when": "abstract says failed to replicate, did not replicate, or no evidence for a named earlier result",
            "example_pattern": "failed to replicate the effect reported by Author et al.",
            "routing_use": "sufficient relation evidence for pair candidate",
        },
        {
            "strength": "4",
            "evidence_type": "abstract_independent_validation",
            "accepted_when": "abstract identifies a discovery/original cohort or claim and an independent validation/replication cohort",
            "example_pattern": "independent validation of the association reported in the discovery cohort",
            "routing_use": "often native_only or d_equivalent_figure1b depending on metric",
        },
        {
            "strength": "4",
            "evidence_type": "methods_original_study_mapping",
            "accepted_when": "methods identify original materials, protocol, study number, intervention, or endpoint being retested",
            "example_pattern": "we used the original materials and procedure from Experiment 2",
            "routing_use": "sufficient relation evidence when bibliographic target can be resolved",
        },
        {
            "strength": "4",
            "evidence_type": "clinical_confirmatory_trial",
            "accepted_when": "trial explicitly frames itself as larger, confirmatory, multicenter, pragmatic, or phase 3 follow-up of an earlier named trial/result",
            "example_pattern": "a multicenter trial to confirm the benefit observed in the earlier single-center trial",
            "routing_use": "candidate for d_equivalent_figure1b if comparative endpoint values exist",
        },
        {
            "strength": "3",
            "evidence_type": "results_original_replication_comparison",
            "accepted_when": "results compare original and replication effects or show original effect in a forest plot/table",
            "example_pattern": "original d = ...; replication d = ...",
            "routing_use": "sufficient when paired with target identity resolution",
        },
        {
            "strength": "3",
            "evidence_type": "table_pair_mapping",
            "accepted_when": "article, supplement, repository, or source table maps original DOI/result to replication DOI/result",
            "example_pattern": "row containing original_source, replication_source, outcome, effect_size",
            "routing_use": "sufficient when source object is mirrored or route is recorded",
        },
        {
            "strength": "3",
            "evidence_type": "preregistration_protocol",
            "accepted_when": "preregistration or registered-report protocol names the earlier target and planned replication outcome",
            "example_pattern": "preregistered direct replication of Study 1 from Author et al.",
            "routing_use": "sufficient relation evidence; values still need article/data/registry source",
        },
        {
            "strength": "3",
            "evidence_type": "genetics_discovery_replication_cohort",
            "accepted_when": "paper gives explicit discovery-vs-replication or discovery-vs-validation cohort mapping for a named association",
            "example_pattern": "discovery cohort; replication cohort; OR/beta and N by cohort",
            "routing_use": "usually native_only unless a preapproved D-equivalent route exists",
        },
        {
            "strength": "2",
            "evidence_type": "repository_readme",
            "accepted_when": "README/data package says it contains replication data and links original and replication papers, but article relation is not yet verified",
            "example_pattern": "OSF project for direct replication of Author et al.",
            "routing_use": "manual screen or coverage_only until primary source is resolved",
        },
        {
            "strength": "1",
            "evidence_type": "ordinary_citation_or_review_seed",
            "accepted_when": "review or citing paper mentions an original and possible replication without primary paper/source-object evidence",
            "example_pattern": "a review says the result failed to replicate",
            "routing_use": "seed only; not enough for pair inclusion",
        },
        {
            "strength": "0",
            "evidence_type": "no_relation_evidence",
            "accepted_when": "no explicit original/replication, original/follow-up, or discovery/validation mapping is present",
            "example_pattern": "ordinary related literature discussion",
            "routing_use": "reject unless later evidence is found",
        },
        {
            "strength": "-5",
            "evidence_type": "same_data_reanalysis",
            "accepted_when": "paper only reanalyzes, robustness-checks, or runs a multiverse on the same dataset",
            "example_pattern": "reanalysis of the original data",
            "routing_use": "reject for Figure 1 independent-sample rows; keep as context if useful",
        },
        {
            "strength": "-5",
            "evidence_type": "computational_only_reproduction",
            "accepted_when": "paper only reproduces code, benchmark output, or analysis workflow using the same data",
            "example_pattern": "we reproduced the code/results",
            "routing_use": "reject unless a separate computational subplot is intentionally opened",
        },
    ]


def build_routing_score_rules() -> list[dict[str, str]]:
    return [
        {"score_family": "relation", "score": "+5", "condition": "target in title or Registered Replication Report title/metadata", "decision_use": "pair candidate after identity normalization"},
        {"score_family": "relation", "score": "+4", "condition": "abstract says direct replication, failed replication, independent validation, or named confirmatory/follow-up trial", "decision_use": "pair candidate"},
        {"score_family": "relation", "score": "+4", "condition": "methods map original study/result/materials/protocol/endpoint", "decision_use": "pair candidate if original target resolves"},
        {"score_family": "relation", "score": "+3", "condition": "table, supplement, repository, preregistration, or source object maps original and replication sides", "decision_use": "manual screen; candidate when source identity resolves"},
        {"score_family": "relation", "score": "+2", "condition": "repository README/package evidence only", "decision_use": "manual screen or coverage_only until article/source identity resolves"},
        {"score_family": "relation", "score": "+1", "condition": "ordinary citation, review statement, or broad literature context only", "decision_use": "seed_only; insufficient for pair inclusion"},
        {"score_family": "relation", "score": "-5", "condition": "same-data reanalysis or computational-only reproduction", "decision_use": "reject for independent-sample Figure 1 rows"},
        {"score_family": "relation", "score": "-4", "condition": "review/commentary only or no original mapping", "decision_use": "reject or seed_only"},
        {"score_family": "relation_threshold", "score": ">=4", "condition": "affirmative relation evidence", "decision_use": "eligible for pair candidate and value extraction"},
        {"score_family": "relation_threshold", "score": "2-3", "condition": "moderate relation evidence but missing identity/source-object confirmation", "decision_use": "manual_screen or coverage_only"},
        {"score_family": "relation_threshold", "score": "<=1", "condition": "weak or no relation evidence", "decision_use": "seed_only or reject"},
        {"score_family": "value", "score": "+5", "condition": "original effect, original N, replication effect, and replication N directly reported", "decision_use": "extract values from source_result rows and route by metric"},
        {"score_family": "value", "score": "+4", "condition": "all values reconstructable from means/SDs, t/F/r, event counts, OR/logOR, RR/RD with baseline risk, or registry result tables", "decision_use": "extract and document conversion formula"},
        {"score_family": "value", "score": "+3", "condition": "effects available but split N or aggregation grain unclear", "decision_use": "hold with blocker or route coverage/native after review"},
        {"score_family": "value", "score": "+2", "condition": "N available but one side effect missing", "decision_use": "coverage_only unless source object can be acquired"},
        {"score_family": "value", "score": "+1", "condition": "relation exists but values are inaccessible/paywalled/missing", "decision_use": "coverage_only no-repull ledger"},
        {"score_family": "value", "score": "-5", "condition": "one-arm overall response rate or no comparator for binary endpoint", "decision_use": "reject for Figure 1B"},
        {"score_family": "route", "score": "relation>=4 and value>=4", "condition": "D/SMD-compatible inputs and independent larger replication sample", "decision_use": "strict_figure1a"},
        {"score_family": "route", "score": "relation>=4 and value>=4", "condition": "comparative binary inputs with defensible logOR/OR/RR/RD-to-D route", "decision_use": "d_equivalent_figure1b"},
        {"score_family": "route", "score": "relation>=4 and value>=4", "condition": "native effects/N available but no defensible D route", "decision_use": "native_only"},
        {"score_family": "route", "score": "relation>=4 and value<=2", "condition": "real pair exists but public values/source objects are missing or inaccessible", "decision_use": "coverage_only"},
    ]


def build_query_log_schema() -> list[dict[str, str]]:
    fields = [
        ("query_id", "stable query identifier from the generated query bank"),
        ("run_id", "date/versioned run identifier"),
        ("surface", "OpenAlex, Crossref, PubMed, PMC, PLOS, OSF, Figshare, Dataverse, Zenodo, GitHub, web, or other surface"),
        ("endpoint_or_engine", "API endpoint, CLI command, or search engine used"),
        ("query_family", "campaign phase/query type from the query bank"),
        ("query_string", "exact query string sent to the surface"),
        ("params_json", "surface-specific parameters, filters, fields, page size, cursor, sort, and date filters"),
        ("date_run", "ISO date/time for the query"),
        ("cursor_or_page", "cursor, offset, page, or rank window requested"),
        ("rank_start", "first result rank screened"),
        ("rank_end", "last result rank screened"),
        ("n_returned", "number of raw records returned by the surface"),
        ("n_new_work_ids", "number of normalized works not already seen"),
        ("n_new_candidate_pairs", "number of candidate original/replication pairs emitted"),
        ("raw_output_path", "repo-relative path to raw JSON/XML/HTML/TSV response"),
        ("notes", "blockers, API limits, high-noise terms, or recall-probe misses"),
    ]
    return [{"field": field, "description": description} for field, description in fields]


def build_design_contract(
    query_rows: list[dict[str, str]],
    recall_probes: list[dict[str, str]],
    relation_evidence_rows: list[dict[str, str]],
    routing_score_rows: list[dict[str, str]],
    query_log_rows: list[dict[str, str]],
) -> dict[str, object]:
    phase_counts: dict[str, int] = {}
    phase_surfaces: dict[str, set[str]] = {}
    for row in query_rows:
        phase = row["campaign_phase"]
        phase_counts[phase] = phase_counts.get(phase, 0) + 1
        phase_surfaces.setdefault(phase, set()).add(row["surface"])
    query_phases = [
        {
            "campaign_phase": phase,
            "n_queries": phase_counts[phase],
            "surfaces": sorted(phase_surfaces[phase]),
        }
        for phase in sorted(phase_counts)
    ]
    route_labels = {
        "strict_figure1a": {
            "include_when": [
                "independent original and replication/follow-up samples",
                "specific original result maps to specific replication/follow-up result",
                "original_N and replication_N available",
                "both effects are D/SMD-compatible or documented statistic-to-D conversions",
                "replication_N_total greater than original_N_total under current Figure 1 rule",
                "not same-data reanalysis or computational-only reproduction",
            ],
            "value_route": "native_d, means_sds_to_d, t_to_d, f_to_d, r_to_d only when codebook policy permits",
        },
        "d_equivalent_figure1b": {
            "include_when": [
                "comparative binary or clinical endpoint",
                "event counts by arm or OR/logOR/RR/RD with baseline risk sufficient for D-equivalent conversion",
                "original_N and replication_N available",
                "explicit original/follow-up relation evidence",
            ],
            "value_route": "event_counts_to_logor_to_d, or_to_d, rr_with_baseline_to_or_to_d",
        },
        "native_only": {
            "include_when": [
                "strong original/replication relation evidence",
                "native effects and N are available for both sides",
                "no defensible current D or D-equivalent route",
            ],
            "value_route": "retain native metric without plotting on strict D axis",
        },
        "coverage_only": {
            "include_when": [
                "real original/replication or original/follow-up pair exists",
                "relation evidence is strong",
                "public values are missing, inaccessible, paywalled, or insufficient for routing",
            ],
            "value_route": "no-repull target ledger; do not silently drop",
        },
        "manual_screen": {
            "include_when": [
                "relation_score 2-3 or conflicting source/object identity",
                "original target, outcome grain, or source-object route needs human decision",
            ],
            "value_route": "hold before source-object mirroring",
        },
        "seed_only": {
            "include_when": [
                "ordinary citation, review statement, or repository hint points to possible primary papers but does not itself establish the pair",
            ],
            "value_route": "use for snowballing only",
        },
        "reject": {
            "include_when": [
                "same-data reanalysis",
                "computational-only reproduction",
                "review/commentary only with no primary pair resolved",
                "ordinary citing paper without affirmative relation evidence",
                "one-arm ORR or no comparator for binary route",
                "no mappable original result",
            ],
            "value_route": "retain reject reason for dedupe and no-repull audit",
        },
    }
    return {
        "schema_version": "0.1.0",
        "generated_by": str(Path("scripts/build_individual_replication_search_strategy.py")),
        "strategy_id": "figure1_individual_replication_paper_level_search",
        "updated": "2026-05-05",
        "goal": "Find individual paper-to-paper replication, validation, retest, or larger follow-up pairs after corpus/database saturation.",
        "non_goals": [
            "Do not harvest broad replication corpora as final rows in this lane.",
            "Do not count ordinary citations as replication relation evidence.",
            "Do not promote same-data reanalyses or computational-only reproductions as independent-sample Figure 1 rows.",
        ],
        "unit_of_work": {
            "grain": "original_work x replication_work x original_study_result x replication_study_result x outcome x contrast_timepoint x aggregation_level",
            "required_identity_parts": [
                "original_work",
                "replication_work",
                "original_study_result",
                "replication_study_result",
                "outcome",
                "contrast_timepoint",
                "aggregation_level",
            ],
            "pair_key_components": [
                "normalized_original_work_id",
                "normalized_replication_work_id",
                "original_study_label",
                "replication_study_label",
                "outcome_label",
                "contrast_label",
                "timepoint_label",
                "aggregation_level",
            ],
        },
        "core_pipeline": [
            {"order": 1, "step": "raw_hit", "exit_artifact": "raw/{surface}/{query_id}.jsonl"},
            {"order": 2, "step": "candidate_replication_or_followup_paper", "exit_artifact": "works/work_identity.jsonl"},
            {"order": 3, "step": "resolved_original_target", "exit_artifact": "pairs/candidate_pairs.jsonl"},
            {"order": 4, "step": "paper_pair_candidate", "exit_artifact": "pairs/screening_queue.tsv"},
            {"order": 5, "step": "study_outcome_level_pair", "exit_artifact": "individualrepsearch-*.json"},
            {"order": 6, "step": "value_extraction", "exit_artifact": "individual-paper-value-scan-batch001.tsv"},
            {"order": 7, "step": "routing_label", "exit_artifact": "individual-paper-worklist-*.tsv or rejection ledger"},
        ],
        "search_surfaces": [
            "OpenAlex",
            "Crossref",
            "Semantic Scholar",
            "PubMed",
            "Europe PMC",
            "PMC full text",
            "PLOS full text",
            "ClinicalTrials.gov",
            "OSF",
            "DataCite",
            "Zenodo",
            "Figshare",
            "Dataverse",
            "Dryad",
            "ICPSR",
            "GitHub",
            "institutional repositories",
            "manual web search",
        ],
        "query_phases": query_phases,
        "route_labels": route_labels,
        "relation_evidence": {
            "minimum_pair_candidate_score": 4,
            "manual_screen_score_range": "2-3",
            "seed_or_reject_score_range": "<=1",
            "scale_artifact": str(RELATION_EVIDENCE_TSV.relative_to(ROOT)),
            "rows": relation_evidence_rows,
        },
        "routing_scores": {
            "rules_artifact": str(ROUTING_SCORE_TSV.relative_to(ROOT)),
            "rows": routing_score_rows,
        },
        "identity_normalization": {
            "work_key_priority": [
                "normalized DOI",
                "PMID",
                "PMCID",
                "OpenAlex work ID",
                "Semantic Scholar paperId or corpusId",
                "Crossref title-author-year fuzzy key",
                "repository DOI or OSF/Zenodo/Dataverse/Figshare stable identifier",
            ],
            "doi_normalization": [
                "lowercase",
                "strip https://doi.org/ and http://dx.doi.org/",
                "strip doi: prefix",
                "trim trailing punctuation",
            ],
            "title_fuzzy_merge_policy": {
                "auto_merge_threshold": ">=95 token-sort/token-set similarity after normalization",
                "review_threshold": "85-94",
                "no_merge_threshold": "<85",
            },
        },
        "value_extraction": {
            "relation_before_value_rule": "Do not extract/promote Figure 1 values unless relation_score >= 4 or a manual review explicitly upgrades the relation.",
            "source_priority": [
                "article main text/table",
                "supplementary tables",
                "repository data/code",
                "trial registry results",
                "prior meta-science table as pointer only, not final source",
            ],
            "required_verbatim_fields": [
                "verbatim_effect_text",
                "verbatim_n_text",
                "verbatim_source_row_text",
                "source_locator",
                "conversion_explanation",
            ],
        },
        "stop_expand_rules": {
            "stop_query_family_when_all": [
                "all relevant recall probes are rediscovered",
                "two consecutive batches add fewer than 1-2 accepted relation candidates per 500 screened",
                "new accepted pairs are already found by at least two other surfaces",
                "citation-forward expansion yields no new unique candidates",
            ],
            "expand_query_family_when_any": [
                "a recall probe is missed",
                "a domain has many seed-only review mentions but few primary papers",
                "repository hits reveal unsearched article titles or DOIs",
                "clinical/genetics candidates use confirm, validate, retest, or follow-up rather than replicate language",
            ],
        },
        "query_log": {
            "schema_artifact": str(QUERY_LOG_SCHEMA_TSV.relative_to(ROOT)),
            "fields": [row["field"] for row in query_log_rows],
        },
        "recall_probes": {
            "artifact": str(RECALL_PROBES_TSV.relative_to(ROOT)),
            "n_probes": len(recall_probes),
            "probe_ids": [row["probe_id"] for row in recall_probes],
        },
        "generated_artifacts": [
            str(STRATEGY_TSV.relative_to(ROOT)),
            str(VAST_QUERY_TSV.relative_to(ROOT)),
            str(RECALL_PROBES_TSV.relative_to(ROOT)),
            str(RELATION_EVIDENCE_TSV.relative_to(ROOT)),
            str(ROUTING_SCORE_TSV.relative_to(ROOT)),
            str(QUERY_LOG_SCHEMA_TSV.relative_to(ROOT)),
            str(DESIGN_YML.relative_to(ROOT)),
            str(VAST_RUN_PLAN_MD.relative_to(ROOT)),
            str(SCHEMA_JSON.relative_to(ROOT)),
            str(README_MD.relative_to(ROOT)),
            str(VAST_PROMPT.relative_to(ROOT)),
        ],
        "make_targets": [
            "figure1-individual-replication-search-strategy",
            "figure1-individual-replication-vast-search-batch001",
            "figure1-individual-replication-search-intake",
            "figure1-individual-replication-mirror-batch001",
            "figure1-individual-replication-value-scan-batch001",
            "figure1-individual-replication-promote-ready",
        ],
    }


def write_vast_run_plan(query_rows: list[dict[str, str]]) -> None:
    by_phase: dict[str, int] = {}
    for row in query_rows:
        by_phase[row["campaign_phase"]] = by_phase.get(row["campaign_phase"], 0) + 1
    lines = [
        "# Figure 1 Individual Replication Vast Search Plan",
        "",
        "This plan starts after the cheap corpus/database route is saturated. The goal is no longer to find another many-row dataset; it is to find individual papers that explicitly replicate, validate, retest, or definitively follow up an earlier paper/result.",
        "",
        "## Why This Is Different From The GPT Lead Prompts",
        "",
        "The earlier GPT prompts were seed discovery: useful for named leads, but not a measured search over literature surfaces. The vast search has to be recall-auditable. Every query family writes a manifest, every manifest runs through the same dedupe gate, and known-good probes check whether the search recovers famous paper-level replications before we interpret misses as absence.",
        "",
        "## Unit Of Work",
        "",
        "The candidate unit is not just a replication paper. It is:",
        "",
        "```text",
        "original_work x replication_work x original_study/result x replication_study/result x outcome x contrast/timepoint x aggregation_level",
        "```",
        "",
        "The pipeline is:",
        "",
        "```text",
        "raw hit -> candidate replication/follow-up paper -> resolved original target -> paper-pair candidate -> study/outcome-level pair -> value extraction -> routing label",
        "```",
        "",
        "Relation discovery is separate from value extraction. A paper becomes a pair candidate only after affirmative evidence says it is replicating, validating, retesting, or definitively following up a specific earlier result. Value extraction then determines strict Figure 1A, D-equivalent Figure 1B, native-only, coverage-only, or reject routing.",
        "",
        "## Campaign Order",
        "",
        "1. Run known-good recall probes against the query bank. If famous paper-level replications are missed, expand the phrase family before mining long-tail results.",
        "2. Run metadata phrase searches in OpenAlex, Crossref, Semantic Scholar, PubMed, and EuropePMC. Capture titles/abstracts and DOI/PMID/PMCID IDs.",
        "3. Run open full-text value-language searches in PMC, PLOS, and EuropePMC. Prioritize hits that expose D/statistic/N text.",
        "4. Run repository package searches in OSF, Figshare, Dataverse, Zenodo, GitHub, and Dryad. Accept packages only when they identify a paper-level original/replication relation or source values.",
        "5. Run citation-forward searches from known original papers and from unresolved current Figure 1 side targets. Filter citing papers for replication language.",
        "6. Run domain lanes: psychology long tail, behavioral economics/marketing/management, education/health/sports, clinical follow-up, and genetics validation.",
        "7. Apply negative filters for same-data reanalyses, computational-only reproductions, and review-only records.",
        "8. Save candidates as `individualrepsearch-*.json`, then run `make figure1-individual-replication-search-intake`.",
        "",
        "## Query Bank Summary",
        "",
    ]
    for phase, count in sorted(by_phase.items()):
        lines.append(f"- `{phase}`: {count} queries")
    lines.extend(
        [
            "",
            "## Promotion Gates",
            "",
            "- Strict Figure 1A requires original D-compatible effect, original N, replication D-compatible effect, replication N, and a larger replication/follow-up N under the current rule.",
            "- Figure 1B D-equivalent requires comparative binary inputs such as event counts, OR/logOR, RR/RD with baseline risk, and documented conversion.",
            "- Native-only rows preserve useful paper pairs that cannot be put on the D axis.",
            "- Coverage-only rows prove a target exists and should not be re-pulled, even if public values are missing.",
            "- Reject same-data reanalyses, generic reviews, one-arm ORR without comparator, and ordinary citations without affirmative replication relation evidence.",
            "",
            "Use the relation-evidence scale and routing-score rules as the screening contract:",
            "",
            f"- Design YAML: `{DESIGN_YML.relative_to(ROOT)}`",
            f"- Relation evidence scale: `{RELATION_EVIDENCE_TSV.relative_to(ROOT)}`",
            f"- Routing score rules: `{ROUTING_SCORE_TSV.relative_to(ROOT)}`",
            f"- Query log schema: `{QUERY_LOG_SCHEMA_TSV.relative_to(ROOT)}`",
            "",
            "## Stop Or Expand Rules",
            "",
            "- Stop a query family only when relevant recall probes are recovered, two consecutive batches add fewer than 1-2 accepted relation candidates per 500 screened, and citation expansion from accepted pairs yields no new unique candidates.",
            "- Expand when a recall probe is missed, a domain has many seed-only review mentions but few primary papers, repository hits reveal unsearched article titles/DOIs, or candidates use confirm/validate/retest language rather than replicate language.",
            "- Record every query in the query log. Do not silently drop false positives; write reject reasons or coverage/native blockers so future searches can dedupe them.",
            "",
            "## Output Artifacts",
            "",
            f"- Design YAML: `{DESIGN_YML.relative_to(ROOT)}`",
            f"- Query bank TSV: `{VAST_QUERY_TSV.relative_to(ROOT)}`",
            f"- Known-good recall probes: `{RECALL_PROBES_TSV.relative_to(ROOT)}`",
            f"- Relation evidence scale: `{RELATION_EVIDENCE_TSV.relative_to(ROOT)}`",
            f"- Routing score rules: `{ROUTING_SCORE_TSV.relative_to(ROOT)}`",
            f"- Query log schema: `{QUERY_LOG_SCHEMA_TSV.relative_to(ROOT)}`",
            f"- Candidate schema: `{SCHEMA_JSON.relative_to(ROOT)}`",
            f"- Intake README: `{README_MD.relative_to(ROOT)}`",
        ]
    )
    VAST_RUN_PLAN_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_vast_prompt() -> None:
    VAST_PROMPT.write_text(
        "\n".join(
            [
                "# Figure 1 Individual Replication Vast Search Prompt - 2026-05-05",
                "",
                "Use this prompt when asking GPT/Gemini/Deep Research or a human assistant to run a systematic paper-level search after corpus/database saturation.",
                "",
                "## Goal",
                "",
                "Find individual paper-to-paper replication, validation, retest, or larger follow-up pairs that can be routed into Figure 1A strict D/N rows, Figure 1B D-equivalent binary/clinical rows, native-effect retention rows, or coverage-only/no-repull ledgers.",
                "",
                "This is not a request for more replication corpora. It is a recall-auditable search over bibliographic metadata, open full text, repositories, citation-forward links, and domain-specific paper lanes.",
                "",
                "The candidate grain is `original_work x replication_work x original_study/result x replication_study/result x outcome x contrast/timepoint x aggregation_level`. Do not collapse a multi-study paper pair into one row unless the source itself reports a pooled estimate at that same aggregation level.",
                "",
                "## Required Search Surfaces",
                "",
                "Use as many of these as available in your environment:",
                "",
                "- OpenAlex, Crossref, Semantic Scholar, PubMed, EuropePMC, and Google Scholar-style metadata search.",
                "- PMC, PLOS, EuropePMC, and open publisher full-text search.",
                "- OSF, Figshare, Dataverse, Zenodo, GitHub, Dryad, ICPSR, and institutional repositories.",
                "- ClinicalTrials.gov/PubMed trial pages for larger clinical follow-ups.",
                "- Citation-forward search from known original papers and citation-backward search from candidate replication papers.",
                "",
                "## Query Campaign",
                "",
                f"Use the design contract in `{DESIGN_YML.relative_to(ROOT)}` and the query families in `{VAST_QUERY_TSV.relative_to(ROOT)}`. Start with priority 1 and 2 rows. Before long-tail mining, check the recall probes in `{RECALL_PROBES_TSV.relative_to(ROOT)}`.",
                "",
                "If a query family fails to recover obvious probes such as power posing, Bem/Ritchie, goal priming, physical warmth, or analytic-thinking/religion, expand that phrase family before continuing.",
                "",
                "## Candidate Rules",
                "",
                "Accept a lead only when there is affirmative original/replication relation evidence: self-described replication, registered replication report, failed-to-replicate article, larger confirmatory trial, independent validation, or a source table/data package that explicitly maps original and replication sides.",
                "",
                f"Score relation evidence using `{RELATION_EVIDENCE_TSV.relative_to(ROOT)}` and `{ROUTING_SCORE_TSV.relative_to(ROOT)}`. Relation score must be at least 4 before value extraction. A lower score is seed-only or manual screen, not a Figure 1 candidate.",
                "",
                "Reject or route away from Figure 1A when the hit is only a review, same-data reanalysis, computational-only reproduction, ordinary citation, one-arm ORR without comparator, or a clinical development sequence with no explicit same/close endpoint follow-up relation.",
                "",
                "## Output",
                "",
                "Return JSON only, using the schema in `steps/searches/figure1/individualrepsearch-candidate-schema.json`. Include:",
                "",
                "- original and replication bibliographic identities, including DOI/PMID/PMCID/NCT/URLs where available;",
                "- source-object URLs to mirror first;",
                "- relationship evidence and where it was seen;",
                "- whether original effect, original N, replication effect, and replication N are available;",
                "- effect metric and conversion route;",
                "- dedupe risk and likely overlap with existing source families;",
                "- high-confidence rejections and the exact reason;",
                "- searches run, including query text, search surface, useful hits, and notes.",
                "",
                "Batch size target: 25-75 candidate leads per returned manifest, with high precision. Use separate manifests by surface or campaign phase when possible, for example `individualrepsearch-openalex-direct-language-batch001.json` or `individualrepsearch-osf-source-packages-batch001.json`.",
                "",
                "## After Return",
                "",
                "Save the JSON under `steps/searches/figure1/individualrepsearch-*.json`, then run:",
                "",
                "```text",
                "make figure1-individual-replication-search-intake",
                "make figure1-individual-replication-mirror-batch001",
                "make figure1-individual-replication-value-scan-batch001",
                "make figure1-individual-replication-promote-ready",
                "```",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "Figure 1 individual replication search manifest",
    "type": "object",
    "required": ["task_id", "candidates"],
    "properties": {
        "task_id": {"type": "string"},
        "batch_id": {"type": "string"},
        "candidates": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["candidate_id", "candidate_name", "candidate_route"],
                "properties": {
                    "candidate_id": {"type": "string"},
                    "candidate_name": {"type": "string"},
                    "domain": {"type": "string"},
                    "candidate_route": {
                        "enum": [
                            "strict_figure1a",
                            "strict_d",
                            "figure1a",
                            "d_equivalent_figure1b",
                            "d_equivalent",
                            "figure1b",
                            "native_only",
                            "native_scale_subplot",
                            "coverage_only",
                            "coverage_worklist",
                            "manual_screen",
                            "seed_only",
                            "likely_exclude",
                            "reject"
                        ]
                    },
                    "confidence": {"enum": ["high", "medium", "low"]},
                    "candidate_unit_key": {"type": "string"},
                    "screening_status": {"type": "string"},
                    "query_ids": {"type": "array", "items": {"type": "string"}},
                    "surfaces": {"type": "array", "items": {"type": "string"}},
                    "raw_record_paths": {"type": "array", "items": {"type": "string"}},
                    "original_work": {"type": "object"},
                    "replication_work": {"type": "object"},
                    "original_study_result": {"type": "object"},
                    "replication_study_result": {"type": "object"},
                    "outcome": {"type": "object"},
                    "contrast": {"type": "object"},
                    "timepoint": {"type": "string"},
                    "aggregation_level": {"type": "string"},
                    "relation_score": {"type": ["number", "string", "null"]},
                    "value_score": {"type": ["number", "string", "null"]},
                    "relation_evidence_strength": {"type": ["number", "string", "null"]},
                    "relation_evidence_type": {"type": "string"},
                    "same_data_reanalysis_flag": {"type": "boolean"},
                    "computational_only_flag": {"type": "boolean"},
                    "original_title": {"type": "string"},
                    "original_doi": {"type": "string"},
                    "replication_title": {"type": "string"},
                    "replication_doi": {"type": "string"},
                    "conversion_route": {"type": "string"},
                    "source_object_urls": {"type": "array", "items": {"type": "string"}},
                    "dedupe_terms": {"type": "array", "items": {"type": "string"}},
                    "original": {"type": "object"},
                    "replication_or_followup": {"type": "object"},
                    "replication": {"type": "object"},
                    "relation": {"type": "object"},
                    "relationship_evidence": {"type": "object"},
                    "relation_evidence": {"type": "array"},
                    "values": {"type": "object"},
                    "conversion": {"type": "object"},
                    "value_availability": {"type": "object"},
                    "source_objects_to_mirror_first": {"type": "array"},
                    "blockers": {"type": "array"},
                    "reject_reason": {"type": ["string", "null"]},
                    "recommended_next_action": {"type": "string"},
                },
            },
        },
        "searches_run": {"type": "array"},
        "high_confidence_rejections": {"type": "array"},
    },
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--replace", action="store_true")
    parser.parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    query_rows = build_query_bank()
    recall_probes = build_recall_probes()
    relation_evidence_rows = build_relation_evidence_scale()
    routing_score_rows = build_routing_score_rules()
    query_log_rows = build_query_log_schema()
    design_contract = build_design_contract(
        query_rows,
        recall_probes,
        relation_evidence_rows,
        routing_score_rows,
        query_log_rows,
    )
    pd.DataFrame(TRACKS).to_csv(STRATEGY_TSV, sep="\t", index=False)
    pd.DataFrame(query_rows).to_csv(VAST_QUERY_TSV, sep="\t", index=False)
    pd.DataFrame(recall_probes).to_csv(RECALL_PROBES_TSV, sep="\t", index=False)
    pd.DataFrame(relation_evidence_rows).to_csv(RELATION_EVIDENCE_TSV, sep="\t", index=False)
    pd.DataFrame(routing_score_rows).to_csv(ROUTING_SCORE_TSV, sep="\t", index=False)
    pd.DataFrame(query_log_rows).to_csv(QUERY_LOG_SCHEMA_TSV, sep="\t", index=False)
    DESIGN_YML.write_text(yaml.safe_dump(design_contract, sort_keys=False), encoding="utf-8")
    SCHEMA_JSON.write_text(json.dumps(SCHEMA, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    README_MD.write_text(
        "\n".join(
            [
                "# Figure 1 Individual Replication Search Intake",
                "",
                "Save GPT/Gemini/tool outputs as `steps/searches/figure1/individualrepsearch-*.json`.",
                "Each manifest should follow `individualrepsearch-candidate-schema.json`.",
                "",
                "Run:",
                "",
                "```text",
                "make figure1-individual-replication-search-intake",
                "make figure1-individual-replication-mirror-batch001",
                "make figure1-individual-replication-value-scan-batch001",
                "make figure1-individual-replication-promote-ready",
                "```",
                "",
                "The intake step dedupes against the current Figure 1 pair/BibTeX maps before any source-object mirroring or row promotion.",
                "",
                "For the broad paper-level campaign, start with:",
                "",
                "```text",
                f"{VAST_RUN_PLAN_MD.relative_to(ROOT)}",
                f"{DESIGN_YML.relative_to(ROOT)}",
                f"{VAST_QUERY_TSV.relative_to(ROOT)}",
                f"{RECALL_PROBES_TSV.relative_to(ROOT)}",
                f"{RELATION_EVIDENCE_TSV.relative_to(ROOT)}",
                f"{ROUTING_SCORE_TSV.relative_to(ROOT)}",
                f"{QUERY_LOG_SCHEMA_TSV.relative_to(ROOT)}",
                "```",
                "",
                "Screening grain: original_work x replication_work x original_study/result x replication_study/result x outcome x contrast/timepoint x aggregation_level.",
                "",
                "Relation discovery is separate from value extraction. Do not route a paper into Figure 1 unless it has affirmative relation evidence under the relation scale and enough value support for the selected route.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    write_vast_run_plan(query_rows)
    write_vast_prompt()
    print(f"Wrote {STRATEGY_TSV}")
    print(f"Wrote {VAST_QUERY_TSV}")
    print(f"Wrote {RECALL_PROBES_TSV}")
    print(f"Wrote {RELATION_EVIDENCE_TSV}")
    print(f"Wrote {ROUTING_SCORE_TSV}")
    print(f"Wrote {QUERY_LOG_SCHEMA_TSV}")
    print(f"Wrote {DESIGN_YML}")
    print(f"Wrote {VAST_RUN_PLAN_MD}")
    print(f"Wrote {VAST_PROMPT}")
    print(f"Wrote {SCHEMA_JSON}")
    print(f"Wrote {README_MD}")


if __name__ == "__main__":
    main()
