# Current Step-by-Step Strategy for the 300-Row Provenance Sample

Date: 2026-05-01

## Executive Summary

The current strategy is no longer a generic web-scraping pass. It is a staged provenance escalation system for a fixed 300-row pilot. Each plotted row starts as a source-result assertion from a corpus, registry, replication project, or derived table. The goal is to preserve that assertion while progressively adding better source objects: first an identifiable represented work, then local bytes for the represented source, then exact effect and sample-size verification from those bytes. We are using the evidence ladder strictly: level 3 is an external assertion with enough target identity to find the represented work, level 4 is independent grounding by DOI, PMID, PMCID, NCT, AEA, Crossref, or a stable URL, level 5 is local mirroring of a value-bearing source object, level 6 is exact D/N extraction from the original or authoritative source object, and level 7 would be recomputation from raw data or code.

On the current 300-row sample, the strategy is working well at the source-object acquisition layer. The present codebook-shaped `source_result` table has 88 rows at level 6, 167 rows at level 5, 37 rows at level 4, and 8 rows at level 2. In other words, 255 of 300 rows, or 85.0 percent, now have either exact original-source value verification or a mirrored source object. The remaining 45 rows are still below strict level 5 and remain the active tail. Those 45 split into five practical buckets: 17 need Metabus or shorthand citation crosswalks, 13 need manual capture, 8 need identity crosswalks, 4 have exhausted public and CORE routes, and 3 need better identifiers.

The central lesson is that breadth-first acquisition works until the tail. General metadata APIs and open-access routes moved most grounded rows to level 5, especially ClinicalTrials.gov records, PMC/Europe PMC XML, OpenAIRE, OpenAlex, Crossref full-text links, Unpaywall, CORE, OSF, Wayback, and Semantic Scholar. The remaining failures are not all "missing PDFs"; many are identity failures. Several rows are shorthand citations such as `JAP-79-5-691`, anonymized source IDs such as Schaefer/Schwarz workbook handles, or paper-level medians from preregistered result sets. Those cannot honestly be promoted by trying more download URLs alone. They need a crosswalk from corpus-specific handles to actual papers, or a manual acquisition event that records how a human found and mirrored the source object.

## Current Performance on the 300-Row Sample

The grounding stage performed strongly. The real-world grounding pass reports all 300 rows with a source-bibliography real-world URL and all 300 with some real-world URL. It recovered a primary real-world represented-source URL for 297 rows. It found represented identifiers or candidates for 296 rows and high-confidence represented identifiers for 262 rows. Before the later acquisition passes, only 43 rows were level 5 or higher, and 37 of those had exact original-source numeric verification. That baseline made clear that identity grounding and source-object acquisition were separate tasks: a row can be grounded at level 4 without being verified from original source text.

The first strict level-5 probe attempted 242 level-4 rows and made 1,656 fetch attempts. It obtained strict level-5 source objects for 140 rows, found noneligible bytes for 102 rows, and left 102 rows below level 5 at that stage. It also obtained abstract or detail pages for all 242 rows attempted, but the rules correctly prevented metadata pages, abstract pages, DOI landing pages, paywall pages, CAPTCHA pages, and access-denied pages from qualifying as level 5 unless they actually contained the plotted values. The level-5 probe exposed the dominant blockers: 330 blocked HTTP statuses, 105 bot or CAPTCHA blocks, 62 landing or paywall pages, 199 request failures, and 644 support metadata records. It also showed where the system was succeeding: 192 source-object-obtained attempts and 52 ClinicalTrials.gov rows mirrored through registry routes.

The level-6 registry verification pass is the highest-quality success so far. It attempted 89 ClinicalTrials.gov targets and promoted 88 to level 6. Of those, 51 verified plotted D/N values from registry JSON and 37 verified single registry outcomes from JSON. One row had partial child values verified but lacked complete matching p-value evidence. This pass is important because it proves the schema can do more than collect PDFs: it can tie exact plotted numeric values back to authoritative source bytes and explain the transformation path.

The full-article text acquisition passes made the largest gain among paper-like rows. The first full-article pass considered 112 targets, made 221 attempts, and accepted 35 full-article text objects, including 24 via OpenAIRE instance URLs, 5 via Crossref full-text links, 4 via Europe PMC XML, 1 via Europe PMC full-text URL, and 1 via Wayback PDF. A later no-key-expansion pass considered 74 targets, made 137 attempts, and accepted 21 more objects, mostly through OpenAlex location URLs plus one Crossref relation DOI and one Wayback HTML. The CORE-focused pass considered 49 targets, made 88 attempts, and accepted 2 CORE full-text URLs. After those passes, the report showed 164 represented full-article text sources across the sample; the later Zotero re-ingest raised the current `source_file` count to 166 full-article files.

The original PDF acquisition layer was useful but lower yield. It started from 117 below-level-5 rows, found 113 with PDF identifiers, attempted 113 rows, and made 865 attempt rows. It obtained 11 valid PDF candidates. The identity check accepted all 11 candidates, with 10 unique SHA-256 values. Accepted routes were 7 Unpaywall PDFs, 2 Crossref TDM PDFs, 1 Europe PMC PDF, and 1 Semantic Scholar open-access PDF. That pass was deliberately conservative: it logged 214 HTTP 403 blocks, 24 login or paywall pages, 20 HTTP 404s, 18 other HTTP failures, 7 HTML-not-PDF responses, and 3 CAPTCHA or bot blocks. The source-object candidate ledger now records 865 candidate rows from those PDF routes, including 588 metadata records, 214 blocked pages, 24 paywall/login pages, 18 unknown candidates, 11 accepted full-article PDFs, 7 landing or HTML pages, and 3 bot blocks.

The Zotero experiment added a small but meaningful final gain and clarified the correct role for Zotero. The automated Zotero pass targeted 15 `needs_manual_capture` rows and logged 45 attempts: 15 `saveItems`, 15 translation-server web metadata attempts, and 15 `savePage` attempts. It accepted no source objects immediately. The failures were 15 landing-page HTTP 403 responses, 15 translation-web metadata-only results, 14 desktop no-full-text events, and 1 identity failure. However, Zotero downloaded two PDFs late into its storage directory after connector progress had already reported no full text. The storage re-ingest then saw 2 Zotero storage files, matched both through the normal DOI/title identity gate, and promoted both as full-article PDFs. That brought the current sample to 166 full-article source files and reduced the below-level-5 tail from 47 rows in the earlier after-CORE report to 45 rows now.

The current `source_file` table has 327 mirrored or evidence-relevant file rows. By byte class, it includes 104 full registry records, 68 full-article HTML files, 55 full-article PDFs, 54 dataset files, 39 full-article XML files, 4 PMC full-text XML files, 2 supplement files, and 1 unclassified source object. By file role, there are 166 full articles, 104 registry records, 52 derived tables, 2 datasets, 1 archive, 1 supplement, and 1 other file. File origins show the mix of approaches: 128 automated downloads, 118 API responses, 52 internal derived artifacts, 24 publisher files, 3 existing local files, and 2 unknown origins. The provenance model is doing its job: it can distinguish a paper from the access route, a mirrored source object from a metadata route, and a literal result assertion from a later promotion.

## Step-by-Step Strategy Going Forward

Step 1 is to keep the 300-row sample stable. We should not change sample membership while measuring acquisition performance. The benchmark remains `SCHEMA_PILOT_N=300` with the current seed. Quick debugging can use smaller `SCHEMA_PILOT_N` values, but any performance claims should be regenerated on the 300-row sample. The important tables are the codebook-shaped outputs under `data/derived/effect_inflation_dataset/schema_pilot/`, especially `source_result_codebook_sample_300.tsv`, `source_file_codebook_sample_300.tsv`, `source_access_codebook_sample_300.tsv`, `source_access_attempt_codebook_sample_300.tsv`, and `source_object_candidate_codebook_sample_300.tsv`.

Step 2 is to preserve the raw assertion before improving it. Every row should keep the original corpus, registry, or source-result text that supplied the effect, N, p-value, confidence interval, or outcome label. We should not overwrite source text with cleaned values. The fields `extraction_source_id`, `represented_source_id`, `access_id`, `source_file_id`, `source_locator`, `verbatim_source_row_text`, `verbatim_effect_text`, and `verbatim_n_text` carry different meanings and should stay separate. This matters most when a row is still below level 5: the external assertion remains useful audit evidence even when the original paper has not been mirrored.

Step 3 is identity grounding. For every row below level 4, the next action is not file acquisition; it is target identification. The unresolved level-2 rows are dominated by anonymized or corpus-specific handles from Schaefer/Schwarz and Linden-style sources. They need a workbook, supplementary file, appendix, author response, or code artifact that maps IDs such as `schaefer_2019_np_*`, `schaefer_2019_preg_*`, and `linden_YEAR_index` to bibliographic records. Until that mapping exists, those rows remain level 2 because the target source is not independently identifiable. For the Metabus-style shorthand rows, the target is usually encoded in journal abbreviation, volume, issue, and first page. Those should be resolved by a deterministic crosswalk against Metabus metadata, PsycINFO-like bibliographic exports if available, Crossref bibliographic queries, or manual journal archive lookup.

Step 4 is strict source-object acquisition for grounded rows. Once a target is level 4, we attempt source objects in a route order that maximizes reproducibility and minimizes manual effort: local existing mirrors, registry APIs, PMC or Europe PMC full text, Crossref full-text and TDM links, OpenAlex locations, OpenAIRE instances, Unpaywall, CORE, OSF or repository downloads, Semantic Scholar open-access PDFs, Wayback CDX, publisher DOI landing pages, and finally Zotero-assisted local capture. Each route gets its own attempt row. Metadata-only records, access-denied pages, CAPTCHA pages, and paywall pages are acquisition evidence but not level-5 evidence. If they contain useful title, abstract, or detail text, that text should be recorded as support for target location, not as a source-object mirror unless it contains the plotted value.

Step 5 is identity review before promotion. The accepted-source rule should stay conservative. A full article, registry JSON, supplement, data/code file, or repository manuscript can become level 5 only after DOI/title or route-specific identity checks pass. The original PDF pass showed why: broad PDF discovery can retrieve plausible files, but promotion should happen only after the source bytes match the represented source. Zotero storage re-ingest follows the same rule. Zotero may find files that our raw HTTP routes miss, but it is not authority. Zotero files become evidence only after being copied into `data/cache/full_article_text_acquisition/sample_300/`, hashed, and promoted through `source_file`, `source_access`, and `source_access_attempt` rows.

Step 6 is exact value verification. Level 5 is not the end state for publication-grade claims. It means we have mirrored a source object that could contain the value. The next pass should parse source objects for support snippets and exact value checks. The current level-6 success is mostly ClinicalTrials.gov. For articles, the next hard problem is table and text extraction: locate the outcome, copied effect text, copied N text, table row, and conversion inputs, then explain how native text became `D`, `N`, standard errors, or standardized fields. The existing `level6_text_candidate_snippets` pass found candidate hits for 16 source results from 52 source files with a five-page PDF cap. That is a start, but it is not enough for broad article-level verification.

Step 7 is to work the remaining 45-row tail by bucket, not by one more global scraper. The 17 Metabus or shorthand rows need citation crosswalk work. The 8 identity-crosswalk rows need corpus-specific mapping. The 3 better-identifier rows need targeted bibliographic search. The 4 public-and-CORE-exhausted rows are likely manual library, publisher, or author-request cases. The 13 active manual-capture rows should use Zotero Desktop and institutional/browser access where lawful, followed immediately by storage re-ingest and identity-gated promotion. For those rows, record the access barrier and exact route rather than hiding the manual step.

Step 8 is to keep crash recovery simple. The Zotero automated script now checkpoints its attempt TSV after each target row and skips represented sources that already have accepted full-article files. If Zotero or the session crashes, the first recovery action is to run storage re-ingest, because Zotero may have completed downloads after the Python driver saw no attachment. Then rerun the automated pass against the remaining rows. The custom `/oa-pipeline/find-files` Zotero bridge remains experimental and should not be relied on until the plugin appears in the dedicated profile's `extensions.json` and the endpoint returns JSON instead of `No endpoint found`.

## Prompt to GPT for Help

```text
We are working on a reproducible provenance audit for a 300-row sample from an effect-size dataset. The repository uses a strict evidence ladder:

- Level 3: an external source assertion names enough bibliographic or registry information that the target paper/study/trial can theoretically be found.
- Level 4: the represented target is independently grounded through DOI, PMID, PMCID, NCT, AEA, Dataverse, Crossref, another citation database, or a stable independent URL.
- Level 5: the original source object or value-bearing bytes were obtained and mirrored locally, such as full article PDF/XML/HTML, PMC XML, full registry JSON/HTML, supplement, data, code, or repository manuscript.
- Level 6: the exact effect and N values were extracted from that original or authoritative source object.
- Level 7: the value was recomputed from raw data/code.

Current 300-row performance:

- 88 rows are level 6.
- 167 rows are level 5.
- 37 rows are level 4.
- 8 rows are level 2.
- 255/300 rows have exact source verification or a mirrored source object.
- 45 rows remain below strict level 5.

The current source files include 166 full articles, 104 full registry records, 52 derived tables, 2 datasets, 1 archive, 1 supplement, and 1 other file. Full article files include 68 HTML, 55 PDF, 39 XML, and 4 PMC XML files. ClinicalTrials.gov verification worked well: 89 registry targets attempted and 88 promoted to level 6. Full-article acquisition worked through OpenAIRE, OpenAlex, Crossref full-text links, Europe PMC, CORE, OSF, Wayback, Semantic Scholar, Unpaywall, and Crossref TDM links. Zotero Desktop was tested as a lawful local harvester: the automated pass accepted no files immediately, but a later storage re-ingest found 2 late-downloaded PDFs and promoted both through the normal DOI/title identity gate.

Remaining buckets:

- 17 rows need Metabus or shorthand citation crosswalks. Examples look like journal abbreviation plus volume/issue/page handles, such as JAP and PP rows.
- 13 active rows need manual capture. The earlier 15-row manual-capture worklist includes 2 rows that Zotero storage re-ingest has already promoted to level 5.
- 8 rows need identity crosswalks. These include anonymized corpus handles such as Schaefer/Schwarz psychology IDs or Linden-style IDs that do not yet map to a public article.
- 4 rows have exhausted public and CORE routes.
- 3 rows need better identifiers.

Important constraints:

- Do not suggest Sci-Hub, credential sharing, bypassing paywalls, evading CAPTCHAs, or violating publisher terms.
- Metadata pages, DOI landing pages, abstracts, access-denied pages, and paywall pages do not count as level 5 unless the plotted value is actually present on the page.
- Every route tried must be recorded separately as an acquisition attempt.
- Every accepted file must have local path, checksum, source identity, access route, source byte class, and rights/storage notes.
- Original text must be preserved before parsing. Cleaned values are additional fields, not replacements.

Please help with a practical next-step plan for the 45-row tail. I need:

1. A ranked strategy by remaining bucket, with likely yield and why.
2. Specific lawful data sources, APIs, repositories, or bibliographic crosswalks to try for Metabus-style shorthand citations and Schaefer/Schwarz or Linden anonymized IDs.
3. A route plan for the 13 active manual-capture rows, plus the 4 public-and-CORE-exhausted rows, that preserves provenance and distinguishes browser/manual access from automated public retrieval.
4. Suggestions for making Zotero Desktop useful without treating Zotero as provenance authority. In particular, how should we operationalize late storage re-ingest and identify files robustly?
5. A level-6 plan for article PDFs/HTML/XML: how to find effect text, N text, table rows, p-values, CIs, and conversion inputs without overclaiming verification.
6. A concise schema checklist for fields that must be filled when a row is promoted from level 4 to level 5 or from level 5 to level 6.

Please be concrete. Prefer deterministic, auditable steps over broad advice. Flag anything that requires human access, institutional access, author contact, or manual review.
```
