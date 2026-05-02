# Source Acquisition Tools: GPT Response Action Plan

This memo converts the external GPT tool review into repo actions for the 300-row
pilot. It is intentionally pilot-scoped; none of these steps should be scaled to
the full dataset until the 300-row evidence ledgers prove the route is reliable.

## Immediate Recommendation

Do not run another generic discovery pass first. The current bottleneck is
value verification from already mirrored objects and historical source-version
matching.

Track A is source-object parsing. The pilot now has 249 source-file artifacts,
all with local bytes present. Of those, 102 registry artifacts are already
handled by the CT.gov level-6 verifier and 144 still need extraction work. The
worklist is written to:

- `data/derived/effect_inflation_dataset/schema_pilot/level6_source_object_extraction_worklist_sample_300.tsv`
- `reports/level6_source_object_extraction_worklist_sample_300_2026-04-30.md`

Track B is versioned-source matching. The only CT.gov row that did not promote
to level 6 has a mirrored current registry JSON, but two local AACT/KG child
values disagree with the current ClinicalTrials.gov record. The drift ledger is
written to:

- `data/derived/effect_inflation_dataset/schema_pilot/ctgov_registry_version_drift_sample_300.tsv`
- `reports/ctgov_registry_version_drift_sample_300_2026-04-30.md`

## Tool Routes To Add Or Harden

1. AACT historical snapshots and CT.gov history/archive pages.
   Use for CT.gov rows where current API JSON disagrees with local corpus
   values. The first pilot case is `NCT04524598`.

2. Structured XML/JATS parsing.
   Use `lxml`/XPath first on `full_article_xml` and `pmc_fulltext_xml` source
   files. Preserve XPath/table locators and exact copied snippets.

3. PDF cascade.
   Use GROBID for scholarly structure, PyMuPDF/pdfplumber for page text and
   coordinates, and Camelot/Docling for table candidates. OCR should be a last
   resort and should require manual QA before level-6 promotion.

4. Repository and supplement parsing.
   For OSF/Dataverse/Zenodo/Figshare/OpenICPSR artifacts, inventory archive
   members, checksums, versions, and table cells before treating files as value
   evidence.

5. Additional acquisition APIs for stubborn grounded rows.
   Add these as candidate resolvers before any publisher scraping: Crossref TDM
   links, Semantic Scholar datasets/S2ORC, BASE, OpenAIRE, Dissemin/OA.Works,
   Zotero Translation Server, Internet Archive CDX, OpenCitations/Wikidata, DOAJ
   and repository-specific APIs.

## Current Pilot Counts After Applying The First Two Actions

- Level-6 CT.gov verifier: 89 attempted, 88 promotable.
- CT.gov drift ledger: 1 source-result row, 2 child rows needing historical
  source-version resolution.
- Source-object extraction worklist: 249 source files, 144 still needing parser
  work.
- First structured-text candidate pass: 52 XML/HTML source files attempted, 72
  snippet/status rows written, and 16 linked source-result rows with at least
  one candidate label or numeric hit. PDFs were intentionally excluded from the
  default fast pass after pdfplumber proved too slow for the full PDF set.
- Artifact snapshot/fixity audit: 249/249 source-file artifacts have local
  bytes, matching byte sizes, matching SHA-256, source-version IDs, and a
  timestamp. However, 0/249 have concrete upstream snapshot/version IDs such as
  an AACT month, OpenAlex snapshot date, S2 release ID, PubMed baseline/update,
  Unpaywall snapshot date, or Crossref public-data-file vintage.
- Wayback lead smoke test: 20 highest-priority manual tasks queried, 39 URL
  variants checked with the fast Wayback availability endpoint, 2 capture leads
  found. Both were old ClinicalTrials.gov `/ct2/show/` variants; DOI resolver
  URLs produced no useful leads in this small pass.
- Original-PDF acquisition pass: all 117 below-level-5 rows with DOI/PMID/PMCID
  handles attempted, 44 row-level PDF candidates obtained. Successful routes:
  Unpaywall direct/repository PDF 33 rows, Europe PMC PDF 4 rows, Crossref TDM
  PDF links 6 rows, and Semantic Scholar open-access PDF 1 row. This produced
  20 unique PDF SHA-256 values because several source-result rows map to the
  same represented paper.
- Fatcat was tested in the first smoke run and repeatedly timed out, so it was
  disabled for the broader 60-row pass. It should be retried later as a
  lower-throughput archive route rather than kept in the hot path.

The first extraction order should be:

1. `structured_xml_first`: 39 artifacts.
2. `table_or_corpus_file`: 54 artifacts, while keeping corpus evidence separate
   from original-paper evidence.
3. `supplement_first`: 2 artifacts.
4. `html_first`: 13 artifacts.
5. `pdf_cascade`: 36 artifacts.
6. `classify_first`: 1 artifact.

## Promotion Rule

None of these routes should promote a row by itself. Level 6 requires:

1. A source object with local bytes and a stable source-file row.
2. Exact value-bearing text/table/data extracted from that object.
3. A `source_result_support` locator: JSONPath, XPath, page, table, row/column,
   character offset, PDF bbox, or spreadsheet cell.
4. A recomputation or exact rounded match showing that the plotted D/N follows
   from the extracted source values.

## Next Coding Tasks

1. Implement AACT snapshot comparator for CT.gov drift rows.
   Inputs: NCT ID, target outcome title, local p/statistic, local N, suspected
   snapshot date. Output: matching snapshot/date or unresolved drift.

2. Add upstream snapshot/version fields to the artifact/source-version layer.
   Keep the existing local `sha256` field, but add explicit upstream snapshot
   identifiers and snapshot timestamps before scaling beyond the pilot.

3. Implement XML/JATS level-6 candidate extractor.
   Inputs: XML source files and linked source-result rows. Output: candidate
   numeric snippets, XPath locators, table cells, and match status.

4. Implement PDF extraction benchmark on a small slice of the 36 PDFs.
   Use GROBID/PyMuPDF/pdfplumber first, then table tools only where needed.

5. Improve Wayback routing before scaling it.
   Query publisher landing URLs, old CT.gov variants, repository URLs, and
   direct PDFs. DOI resolver URLs alone are low-yield and should not dominate
   the queue.

6. Promote reviewed PDF candidates into the normal `source_file` manifest.
   The PDF pass currently writes candidates to
   `data/cache/original_pdf_acquisition/sample_300`; check identity and tag
   access/share scope, then add accepted files to `source_file.tsv`/
   `source_access_attempt.tsv` so parser work can treat them like the other
   level-5 objects. The project policy is internal storage only: the public DB
   records routes, hashes, paths, metadata, and short extracted support windows,
   not redistributed full documents.

7. Keep acquisition and verification separate.
   A DOI, abstract, Paperclip hit, OpenAlex location, or publisher landing page
   can locate a target, but cannot verify D/N until the value-bearing object is
   mirrored and parsed.
