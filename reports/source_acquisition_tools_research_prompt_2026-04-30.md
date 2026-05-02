# Source Acquisition and Value Verification: Lessons Learned + Research Prompt

Date: 2026-04-30

## Context

We are building a D-vs-N evidence map where every plotted dot should be traceable from a plotted value back to a source-result row, a represented source, source bytes, copied source text, and a documented transformation into standardized D and N.

The current pilot is a 300-row random sample from the plot-level dataset. The sample is intentionally being used as a stress test before scaling to the full corpus.

Relevant local outputs:

- `data/derived/effect_inflation_dataset/schema_pilot/source_result_codebook_sample_300.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/source_file_codebook_sample_300.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/source_access_attempt_codebook_sample_300.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/level6_value_verification_attempts_sample_300.tsv`
- `reports/evidence_dataset_codebook.md`
- `reports/level6_value_verification_sample_300_2026-04-30.md`
- `reports/paperclip_openalex_retry_sample_300_2026-04-30.md`

Current 300-row status after the level-6 CT.gov pass:

| Evidence level | Meaning | Rows |
|---:|---|---:|
| 2 | external source assertion only | 19 |
| 4 | target source independently grounded | 98 |
| 5 | original source object obtained | 95 |
| 6 | original number extracted / D-N verified from source | 88 |

Current value-verification states:

| State | Rows |
|---|---:|
| corpus assertion only | 117 |
| source object obtained but not parsed | 95 |
| D/N verified from source | 88 |

Other pilot facts:

- 300 source-result rows.
- 331 source rows.
- 249 source-file artifact rows.
- 1,711 source-access-attempt rows.
- 1,544 source-result-support rows.
- 263 manual-acquisition-task rows.
- 298 rows have recovered verbatim effect/statistic text from some source row.
- 300 rows have recovered N text from some source row.
- 262 rows remain coded with schema gaps because their current values are still derived/corpus-level rather than original-source verified.
- 88 rows now have `number_verified_by_us=true` and `conversion_verified=true`.

## Evidence Concepts We Need To Preserve

We learned that a single "found source" flag is not enough. We need to keep these states distinct:

1. We have only a corpus assertion, citation, or row-level claim.
2. We can independently ground that represented target source through DOI, PMID, PMCID, NCT, registry ID, URL, or citation database.
3. We obtained a landing page or abstract.
4. We obtained a plausible source object: final article, preprint, author manuscript, registry JSON, supplement, data, code, or repository file.
5. We extracted value-bearing source text/data from that object.
6. We verified or recomputed the plotted D/N from the extracted values.

Important distinction:

- ClinicalTrials.gov, OpenAlex, PubMed, Crossref, Semantic Scholar, Paperclip, CORE, and similar services may prove a source exists or provide a copy/abstract/record.
- They do not automatically prove the plotted number unless the D/N, p-value, N, event count, or other conversion input is present in the mirrored object and we parse it.

## What Worked

### ClinicalTrials.gov API v2

This is currently the strongest value-verification route.

The level-6 verifier attempted 89 CT.gov registry-result rows:

- 37 raw registry outcome rows verified directly from current ClinicalTrials.gov API JSON.
- 51 collapsed CT.gov/NCT dots verified by recomputing the plotted NCT-level median from child registry outcome rows.
- 1 row failed because the local CT.gov KG/AACT-derived p-values do not match the current ClinicalTrials.gov API JSON.

Result: 88/89 CT.gov rows in the pilot are verified at level 6.

Lesson: CT.gov dots split into two types:

- Raw outcome dots: verify the selected outcome title, p-value, enrollment N, and D transformation directly.
- Collapsed trial dots: verify every child outcome row for that NCT, then recompute the paper/trial median exactly.

### Structured Provenance Tables

The source-result / source / source-file / source-access-attempt / source-result-support schema is useful. It exposed real defects that would have been invisible in a plot-only table.

Required objects:

- source-result rows for individual extracted values.
- source rows for papers, registries, corpora, repositories, and databases.
- source-source mappings for "database reports paper result," "registry preregisters study," "repository supports paper," and replication/pre-registration relationships.
- source-file artifacts for each mirrored byte object.
- support rows for the literal snippet, table cell, registry field, page, XPath, or archive member supporting each value.

### Paperclip

Paperclip is useful as a fast literature lookup/index for PMC, preprint, arXiv, and abstract discovery. It helped resolve or reject several low-level rows and was useful for exact DOI checks.

Observed strengths:

- Exact DOI lookup can quickly reject bad candidate DOI guesses.
- Search/lookup across Paperclip's abstract and full-text corpus is useful for source discovery.
- It may help locate preprints or full text that ordinary publisher routes block.

Observed limits:

- Paperclip hits are not enough to verify D/N unless we extract the relevant value-bearing text.
- Coverage is strongest for PMC/bioRxiv/medRxiv/arXiv/OpenAlex abstracts, weaker for paywalled psychology/social-science publisher full text.

### OpenAlex and Other Metadata APIs

OpenAlex moved at least one row from a weak unresolved state to an abstract/source-grounded state. Crossref/DataCite/OpenAlex/Semantic Scholar/PubMed/Europe PMC are useful for identity resolution, DOI/PMID/PMCID bridges, abstract retrieval, OA locations, and preprint/repository leads.

Lesson: metadata APIs are excellent for target grounding and candidate URLs, but they are not sufficient for source-value verification.

### Source-Object Classification

The byte class matters. A `full_article_pdf`, `pmc_fulltext_xml`, `registry_record_full`, `dataset_file`, or `supplement_file` can be a level-5 source object. A `metadata_record`, `publisher_landing_or_abstract`, `paywall_or_login_page`, or `captcha_page` is useful provenance but not level 5 unless it contains the value itself.

## What Failed Or Was Fragile

### Same-Title Matching Is Dangerous

We found two retrace bugs:

1. Pandas groupby `.indices` from a filtered frame was positional inside the filtered frame, not label-based in the full table. Applying those positions back to the full candidate row table attached unrelated child rows.
2. For CT.gov registry results, outcome-title-first matching can attach child rows from another NCT with the same outcome title. Matching must prefer stable paper/unit IDs first, then outcome titles.

Fixes made:

- Use `.groups` rather than `.indices` when indexes will be applied back to the original table.
- Prefer `paper_id` / NCT / represented-source ID before title.

### Cached Acquisition Paths Are Hints, Not Proof

One CT.gov level-5 local path pointed to a wrong NCT after the retrace was corrected. The level-6 verifier now re-derives the NCT from the upstream row and refuses mismatched paths.

Lesson: level-5 acquisition output can become stale after retracing or matching fixes. A verifier must re-check source identity.

### Source-Version Drift

The remaining CT.gov failure is not an access issue. The p-values in our local CT.gov KG/AACT-derived row for `NCT04524598` do not match current ClinicalTrials.gov API JSON. This probably means the KG/AACT source was built from an older or alternate registry snapshot.

Lesson: for registries and databases, "current API JSON" is not always the same source version as the corpus that produced the plotted row. We need versioned registry snapshots or archived API responses.

### Bot Blocks And Paywalls Are Common

Observed blockers include:

- APA Incapsula/bot-block pages.
- LWW/ASA Monitor Cloudflare challenge.
- Publisher paywalls and login pages.
- Abstract-only pages.
- Metadata-only pages with no value-bearing text.

Lesson: these should be logged as acquisition artifacts, not promoted.

### Some Corpora Are Anonymized Or Missing Crosswalks

Remaining low-level examples include:

- Schaefer/Schwarz OSF workbooks and coding PDFs with study IDs, years, subdiscipline, N, and effects but no paper-title/DOI/author crosswalk.
- Linden Study 2 SAV rows with `Year`, `Paper`, `d_random`, and `N_random`, but no paper-title/DOI crosswalk.

Lesson: the blocker is not source acquisition but missing identity crosswalks.

### Large Corpora Need Parent/Child Source Modeling

Many dots come from corpora, meta-analyses, registries, or replication datasets. A corpus can report results about many represented papers. The value source and represented research source can differ.

Example:

- `source_result`: a value copied from a database row.
- `extraction_source`: the database/corpus source where the text/value was copied.
- `represented_source`: the paper/trial/study that the database says the value represents.

We need to track both.

## Known Tools Already Tried Or Integrated

Identifier and metadata:

- Crossref
- DataCite
- DOI content negotiation
- OpenAlex
- Semantic Scholar
- PubMed / NCBI E-utilities
- PMC ID Converter
- Europe PMC
- Unpaywall
- CORE

Registry and repository:

- ClinicalTrials.gov API v2
- AEA RCT Registry snapshots and pages
- OSF
- Dataverse
- Zenodo
- Figshare
- OpenICPSR, partially/manual

Literature and full text:

- Paperclip
- PMC / PMC OA / Europe PMC routes
- direct publisher landing-page attempts
- publisher API hints where available

Local extraction and parsing concepts:

- source-file artifact manifests
- source-access-attempt logs
- source-result support snippets
- exact p-value / z / N recomputation
- paper-level median recomputation from child rows

## What We Need GPT To Help With

We need a research pass focused on tools, services, APIs, datasets, browser workflows, and extraction strategies we may be missing. The goal is not a generic literature review; it is an operational plan for improving source acquisition and value verification at scale.

## Prompt To Send To GPT / Deep Research

You are helping with a reproducible evidence-map project. We need to trace tens of thousands of plotted D-vs-N dots back to source-result rows, represented papers/studies/trials, source bytes, copied source text, and verified transformations into D and N. We have a 300-row pilot and want to improve source acquisition and value verification before scaling.

Current pilot status:

- 300 source-result rows.
- 88 rows verified at level 6: plotted D/N or conversion inputs were recomputed from source objects.
- 95 rows have source objects mirrored but not yet value-parsed.
- 98 rows have independently grounded target sources but no source object/value verification yet.
- 19 rows remain external corpus assertions.
- 249 source-file artifact rows.
- 1,711 access-attempt rows.
- 263 manual acquisition tasks.

Evidence levels we care about:

1. External/corpus assertion only.
2. Target source independently grounded by DOI/PMID/PMCID/NCT/URL/citation database.
3. Landing page or abstract obtained.
4. Plausible source object mirrored: final article, preprint, author manuscript, registry JSON, supplement, data, code, repository file.
5. Value-bearing text/table/data extracted from mirrored object.
6. D/N or conversion inputs verified/recomputed from the source object.

Known successes:

- ClinicalTrials.gov API v2 is excellent. We verified 88/89 CT.gov pilot rows by parsing registry JSON. Raw outcome dots verify directly; collapsed NCT dots require verifying all child outcome rows and recomputing the median.
- Paperclip helped for exact DOI checks and some abstract/full-text discovery across PMC, bioRxiv, medRxiv, arXiv, and OpenAlex abstracts.
- OpenAlex helped ground some targets and find abstracts/OA locations.
- Crossref/DataCite/Semantic Scholar/PubMed/Europe PMC/PMC/CORE/Unpaywall are useful for identity and OA discovery.

Known problems:

- Same-title matching is dangerous; match represented-source ID first.
- Cached acquisition paths are hints, not proof; verifiers must re-check source identity.
- Source-version drift matters. Example: a CT.gov KG/AACT-derived row for `NCT04524598` has p-values that do not match current ClinicalTrials.gov API JSON. We may need exact registry snapshots or archives.
- Publisher bot blocks and paywalls are common. APA Incapsula and LWW/Cloudflare blocked some DOI landing pages.
- Some corpora are anonymized or missing crosswalks, e.g. Schaefer/Schwarz and Linden rows with numeric values but no title/DOI crosswalk.
- Many values come from corpora/databases, not directly from papers, so we need to distinguish extraction source vs represented research source.

Tools already considered/tried:

- Crossref REST and TDM links
- DataCite
- DOI content negotiation
- OpenAlex
- Semantic Scholar
- PubMed / NCBI E-utilities
- PMC ID Converter, PMC OA, Europe PMC
- Unpaywall
- CORE
- ClinicalTrials.gov API v2
- AEA RCT Registry snapshots/pages
- OSF
- Dataverse
- Zenodo
- Figshare
- OpenICPSR, partially/manual
- Paperclip
- direct publisher landing-page attempts

Your task:

1. Identify additional tools, APIs, bulk datasets, browser/search services, scholarly indexes, corpus mirrors, registry archives, repository APIs, table-extraction tools, PDF parsers, OCR tools, and citation-crosswalk resources that could improve source acquisition or value verification.
2. For each candidate, explain:
   - what input identifiers it accepts,
   - what output it provides,
   - whether it helps with target identity, source-object acquisition, value extraction, source-versioning, or crosswalk recovery,
   - legal/access constraints,
   - rate limits or bulk-download options,
   - why it is better than or complementary to tools we already tried,
   - exact URLs/docs/API endpoints,
   - a concrete first test to run on our 300-row pilot.
3. Prioritize tools by expected lift for these blocker groups:
   - source object obtained but not value-parsed,
   - DOI/PMID/PMCID rows with final papers or preprints not yet mirrored,
   - psychology/social-science rows behind APA/SAGE/Wiley/OUP/Taylor & Francis/Elsevier/ScienceDirect/Cambridge/Chicago/Duke/AOM,
   - anonymized corpus rows needing paper-ID crosswalks,
   - CT.gov/AACT/registry version drift,
   - replication corpora and preregistration artifacts.
4. Suggest source-version strategies, especially:
   - ClinicalTrials.gov historical snapshots,
   - AACT snapshots,
   - PubMed/PMC versioning,
   - OpenAlex/Unpaywall/Semantic Scholar snapshots,
   - Internet Archive / DOI landing-page archives,
   - repository versioning for OSF, Dataverse, Zenodo, Figshare, OpenICPSR.
5. Suggest extraction tools and workflows for value verification:
   - PDF text/table extraction,
   - XML/JATS extraction,
   - HTML article extraction,
   - supplement spreadsheet/code parsing,
   - figure/table OCR,
   - exact snippet/table-cell provenance,
   - local mirroring and checksum policies.
6. Suggest ways to use web search, Google Scholar-like tools, Lens/Dimensions/Scopus/Web of Science alternatives, browser automation, institutional access, and human-in-the-loop workflows without violating terms.
7. Identify what we should *not* do because it is brittle, legally risky, or likely to contaminate evidence levels.

Important requirements:

- Do not hallucinate tool capabilities. Cite official documentation or primary sources.
- Distinguish "can locate the target" from "can mirror a source object" from "can verify D/N."
- Distinguish current API records from historical/snapshot records.
- Provide exact API examples or commands where possible.
- Include a ranked one-week implementation plan and a ranked longer-term plan.
- Include a "quick wins" table and a "manual-only / not worth automating yet" table.

Potential tools/categories to investigate, but do not limit yourself to these:

- AACT and ClinicalTrials.gov historical snapshots/archives.
- Lens.org, OpenAIRE, BASE, Internet Archive Scholar, Wikidata, OpenCitations/COCI, OA.mg, DOAJ.
- PubMed baseline/update files, PMC OA bulk, Europe PMC bulk/annotations.
- OpenAlex snapshot, Unpaywall snapshot, Semantic Scholar datasets/S2ORC, CORE bulk options.
- Zotero translators, Crossref TDM URLs, publisher TDM APIs, GROBID, CERMINE, ScienceBeam, Docling, unstructured.io, PyMuPDF, pdfplumber, Camelot, Tabula, Tesseract/OCRmyPDF, Nougat-like scientific PDF parsers.
- OSF API/registrations, AsPredicted, AEA RCT Registry, EGAP, RIDIE, ISRCTN, EUCTR, ANZCTR, WHO ICTRP.
- Browser automation for user-permitted manual access and abstract capture.
- Tools for DOI/citation disambiguation and paper-title crosswalk recovery.

Please return:

- ranked recommendations,
- overlooked tools table,
- blocker-specific strategies,
- source-versioning strategy,
- extraction-tool strategy,
- legal/access cautions,
- concrete commands/API examples,
- exact next experiments on the 300-row pilot,
- expected lift estimates and uncertainty.

## Questions We Specifically Want Answered

1. What are the best sources for historical ClinicalTrials.gov/AACT records so a CT.gov-derived corpus row can be verified against the same registry version that generated it?
2. Are there reliable tools for finding author manuscripts/preprints when DOI landing pages are paywalled or bot-blocked, especially for psychology and social science?
3. Are there underused scholarly indexes or APIs that outperform OpenAlex/Unpaywall/Semantic Scholar/Paperclip for difficult DOI rows?
4. What is the best practical stack for extracting exact D/N-supporting text from PDFs and supplements at scale?
5. How should we use Internet Archive or other web archives as evidence for historical landing pages, abstracts, and registry records?
6. Are Zotero translators or browser-based scholarly metadata extractors useful for acquiring source details where APIs fail?
7. How should we handle corpora that provide numeric values but anonymize or omit paper crosswalks?
8. What manual work should be prioritized because automation is unlikely to solve it?

## Expected Output Format

Use these sections:

1. Executive recommendation.
2. Highest-lift new tools we are not using yet.
3. Tools already used but underused or misused.
4. Blocker-by-blocker strategy.
5. Source-version and archival strategy.
6. Value-extraction strategy.
7. Legal/access risk boundaries.
8. One-week implementation plan.
9. Longer-term implementation plan.
10. Exact commands/API examples.
11. Remaining questions for us.

