# Full-Article Acquisition Process, Current Lessons, and Help Prompt

## Executive Summary

We are building a source-provenance system for a D-vs-N evidence map. Each plotted point needs to move from "some corpus says this result exists" toward "we have the represented original source, and we can point to the exact text, table, registry field, supplement cell, or data object that proves the plotted D and N." The task is not ordinary citation lookup. It is a multi-stage acquisition and verification workflow: identify the represented source, find lawful/reproducible routes to the source bytes, download and checksum those bytes locally, classify the source object, confirm the bytes are actually the right paper or registry record, parse the source, locate the value-bearing evidence, and finally verify or recompute D and N.

The current 300-row pilot now has this evidence distribution:

```text
Level 2: 10   external/corpus assertion only
Level 4: 96   represented source independently grounded, but no original source object yet
Level 5: 106  original source object obtained, not yet D/N-verified from that object
Level 6: 88   original number extracted / verified from source

Level >=5: 194/300
Below level 5: 106/300
```

The important clarification is that "source object obtained" is broader than "PDF obtained." Full article obtained means article text in any usable form: PDF, XML, HTML, or PMC/JATS XML. Other source objects, such as registry JSON, datasets, and supplements, can also be legitimate original evidence, but they should not be counted as "full article obtained." Current source-file inventory:

```text
Full article objects:
47 full_article_pdf
35 full_article_xml
13 full_article_html
4  pmc_fulltext_xml
= 99 full article objects

Non-article source objects:
104 registry_record_full
54  dataset_file
2   supplement_file
1   source_object_unclassified
```

The most successful route so far is structured registry verification. ClinicalTrials.gov-style rows were highly tractable because the source is already structured. We verified 88 of 89 CT.gov-derived rows to level 6. The one failure appears to be source-version drift: the current registry record does not match the corpus-derived value, so the next step there is AACT historical snapshot matching rather than more web search.

For papers, the most important lesson is that finding a PDF is not enough. An early broad PDF acquisition pass downloaded 44 PDFs, but an identity check showed that only 11 were the correct represented source. The other 28 wrong-source PDFs were mostly caused by non-primary DOI/URL leads contaminating the acquisition pool. After tightening acquisition to use primary identifiers only, a clean pass attempted 113 below-level-5 rows with DOI/PMID/PMCID handles, downloaded 11 PDFs, and the identity gate accepted all 11. Those 11 were promoted into `source_file`, raising level >=5 to 194/300.

## What We Are Trying To Prove

The evidence map starts with plotted D-vs-N dots. A dot is not intrinsically trustworthy just because it appears in a dataset. We need to know what the dot represents. A plotted point might come from a trial registry, a published article, an accepted manuscript, a preprint, a supplement, a replication dataset, a meta-analysis workbook, or a corpus row derived from a human-coded article. Those are very different provenance situations.

The strictest target is: for each dot, we can say:

1. This is the represented research source.
2. This is the exact source object we mirrored.
3. This is the local path and SHA-256 checksum for that object.
4. This object is the right paper/trial/dataset, not just a similar citation.
5. This exact passage/table/cell/field contains the D, N, p-value, test statistic, outcome, group count, or conversion input.
6. This is the code/formula by which the plotted D and N were directly copied or recomputed.

That is why the system separates source identity, source acquisition, source-file inventory, text extraction, and value verification. A DOI landing page is not the article. A PubMed abstract is not the article. A registry record is not the paper, though it can be an original source for trial-result values. A downloaded PDF is not automatically the right paper. A full article is not automatically value-bearing. And value-bearing text is not level 6 until the D/N transformation is checked.

## Evidence Scale Used In The Pilot

We flattened the working scale into one practical ladder:

```text
0 no useful lead
1 weak corpus assertion or unresolved extraction trace
2 external/corpus assertion with some source claim
3 citation / URL / abstract / landing-page evidence
4 represented source independently grounded
5 original source object obtained
6 D/N verified from source
```

The working distinction that matters most now is between level 4 and level 5. Level 4 means we know what the source likely is: a DOI, title, PMID, NCT ID, repository URL, or other independent grounding exists. Level 5 means we have mirrored a plausible original source object: full article PDF/XML/HTML, registry JSON, supplement, dataset, code file, or similar. Level 6 means we have actually found and verified the plotted D/N value or its conversion inputs.

For article acquisition, we now use a clearer subcategory: "full article obtained." This ignores format. Full article PDF, full article XML, full article HTML, and PMC/JATS XML all count as article text. They differ technically, but from the evidence-hierarchy perspective they are all full article objects.

Registry JSON, datasets, supplements, and code are tracked separately as non-article original source objects. They can be more valuable than the paper for verification if the result actually comes from a registry, supplement, or analysis file. But they should not inflate a "papers obtained" count.

## Data Model And Why It Changed

Early in the process, there was a risk that `source_access` and `source_access_attempt` would become overloaded. They were being asked to represent access routes, failed attempts, downloaded files, and long-term evidence inventory. That is fragile. We changed the conceptual model so that:

- `source_access` describes a route or access state.
- `source_access_attempt` logs candidate URLs, requests, responses, failures, and decisions.
- `source_file` is the actual artifact manifest: local path, URL, final URL, SHA-256, media type, byte class, and extraction readiness.
- `source_access_right` records internal-only / redistribution / text-extraction decisions.
- `source_result` records the evidence level for a plotted result.
- `source_result_support` is where exact locators should go once values are extracted.

This matters because successful bytes need to be content-addressed and independently auditable. A source-access attempt saying "download succeeded" is not enough. We need a stable `source_file_id`, SHA-256, and byte class. The source file might later be parsed multiple times by different tools. The parser output should always point back to the same file hash.

We also now distinguish "extraction source" from "represented source." Many rows come from corpora. The extraction source might be a meta-analysis workbook, replication dataset, registry-derived table, or corpus spreadsheet. The represented source is the original paper/trial/study that the corpus row stands for. A row can be numerically verified from the corpus and still lack represented-source verification. That distinction prevents us from claiming too much.

## What Codex Did

Codex has been used as a coding agent inside the repository. The implementation is mostly Python scripts operating on TSV manifests under:

```text
data/derived/effect_inflation_dataset/schema_pilot/
```

The workflow has been iterative:

1. Inspect the current schema and codebook.
2. Write focused Python scripts for a single acquisition or validation pass.
3. Run the pass over the 300-row pilot.
4. Write diagnostic TSVs and Markdown reports.
5. Validate the schema against the codebook.
6. Fix incorrect assumptions discovered by the diagnostics.

Important scripts added or used include:

```text
scripts/verify_schema_pilot_level6_values.py
scripts/resolve_ctgov_registry_version_drift.py
scripts/plan_level6_source_object_extraction.py
scripts/extract_level6_text_candidates.py
scripts/audit_artifact_snapshot_provenance.py
scripts/query_wayback_for_manual_tasks.py
scripts/acquire_original_pdfs_pilot.py
scripts/check_original_pdf_identity_pilot.py
scripts/promote_original_pdfs_to_source_file_pilot.py
```

The Makefile now has corresponding targets:

```text
make level6-schema-pilot
make ctgov-version-drift-pilot
make level6-extraction-worklist-pilot
make level6-text-candidates-pilot
make artifact-snapshot-audit-pilot
make wayback-manual-tasks-pilot
make original-pdf-acquisition-pilot
make original-pdf-identity-pilot
make original-pdf-promote-pilot
make validate-schema-pilot
```

This matters because we are not doing one-off manual downloads and losing provenance. Every pass leaves a ledger. Even failed requests are valuable because they explain why a row did not advance: 403, 404, paywall/login HTML, CAPTCHA, HTML-not-PDF, metadata-only, wrong DOI, or needs manual identity check.

## The PDF Acquisition Pass

The focused PDF acquisition pass targeted rows below level 5 that had DOI/PMID/PMCID handles. It tried these routes:

- PubMed eSummary bridge, to recover DOI/PMCID from PMID.
- PMC OA PDF routes for PMCID.
- Europe PMC PDF routes.
- Crossref work metadata, especially `message.link` / TDM links.
- Unpaywall `url_for_pdf` and OA locations.
- OpenAlex `locations`, `best_oa_location`, and `pdf_url` candidates.
- Semantic Scholar `openAccessPdf`.
- DOI resolver with `Accept: application/pdf`.
- Fatcat was considered but disabled by default after timeout behavior in the pilot.

The first broad pass found many PDFs, but it used too many identifier leads. It included non-primary URLs and DOIs from grounding data. That created a serious false-positive problem. For example, `10.1090/noti3044` appeared as a non-primary DOI lead and got downloaded repeatedly for unrelated psychology/economics rows. The downloaded PDFs were real PDFs, but not the represented sources.

This produced the key lesson: "PDF obtained" is not a promotion criterion. "Identity-accepted PDF obtained" is.

We then added `scripts/check_original_pdf_identity_pilot.py`, which uses local command-line PDF tools (`pdftotext`, `pdfinfo`) and primary DOI metadata to check downloaded candidates. The gate records:

- represented source ID
- represented title
- primary DOI(s)
- acquired DOI
- candidate URL DOI(s)
- final URL DOI(s)
- DOI(s) found in extracted PDF text
- title similarity
- token coverage
- SHA-256 match
- identity decision
- identity decision reason

It rejects a PDF if the acquired DOI does not match the primary represented-source DOI. It can accept by primary DOI route plus DOI in PDF text, by primary DOI route plus strong title match, or by primary DOI appearing in PDF text despite route ambiguity. Weak synthetic titles still need caution.

After this, we patched `scripts/acquire_original_pdfs_pilot.py` so it uses primary identifiers only by default. Exploratory non-primary chasing can still be enabled, but any such hit must pass the identity gate before promotion.

## Clean PDF Results

The clean primary-ID-only pass used:

```bash
ORIGINAL_PDF_MAX_ROWS=200 \
PROVENANCE_CONTACT_EMAIL='...' \
UNPAYWALL_EMAIL='...' \
make original-pdf-acquisition-pilot
```

It attempted 113 below-level-5 rows with DOI/PMID/PMCID handles and produced:

```text
attempt_rows: 865
valid PDF candidates: 11
rows_with_pdf_obtained: 11
include_nonprimary_identifiers: false
```

Failure profile:

```text
ok metadata responses:          568
HTTP 403 blocked:               214
login_or_paywall_html:           24
HTTP 404:                        20
HTTP not OK:                     18
pdf_obtained:                    11
html_not_pdf:                     7
captcha_or_bot_block:             3
```

Route successes:

```text
Unpaywall:        7
Crossref TDM:     2
Europe PMC:       1
Semantic Scholar: 1
```

Then:

```bash
make original-pdf-identity-pilot
```

The identity check accepted all 11 and rejected none:

```text
PDF candidate rows checked: 11
Accepted: 11
Rejected wrong source: 0
Needs manual identity check: 0
Unique PDF SHA-256: 10
```

Then:

```bash
make original-pdf-promote-pilot
```

The 11 accepted PDFs were appended to `source_file`, with matching `source_access`, `source_access_attempt`, and `source_access_right` rows. Their corresponding `source_result` rows were promoted to level 5. The final state became:

```text
2: 10
4: 96
5: 106
6: 88
>=5: 194/300
```

Schema validation now passes for the source artifact tables. Remaining validation issues are in `source_result.tsv` and are known source-cell/full-coding/schema-gap issues, not the new PDF manifest rows.

## What Worked

### ClinicalTrials.gov / Registry JSON

This is the clearest success case. Registry rows are structured. NCT ID, outcome title, p-value/statistic fields, group arms, and enrollment/sample size fields can be parsed deterministically. The system can compare plotted values to registry fields and recompute D/N transformations. That is why 88 rows reached level 6.

The main registry problem is not acquisition. It is versioning. ClinicalTrials.gov current API output may differ from the historical state used by a corpus. The correct fix is AACT monthly/daily snapshots and, for individual discrepancies, ClinicalTrials.gov record history. A current JSON mismatch does not necessarily mean the corpus was wrong.

### Full-Article XML / JATS / PMC XML

XML is often better than PDF for verification. It preserves article sections, tables, references, and sometimes table cells. For level 6, XML can provide cleaner locators than PDF text. PMC/Europe PMC/JATS/BioC style objects should be parsed before any PDF parser is used.

### Unpaywall

Unpaywall was the most productive clean PDF route in this sample. It found repository or OA PDF locations for seven accepted PDFs. The lesson is to use it as a source-object route, not merely metadata. But the returned PDF still needs identity validation.

### Crossref TDM Links

Crossref `message.link` / TDM-style full-text URLs produced two accepted PDFs. This route is worth keeping. It can expose direct publisher PDF/XML links that are not the same as the DOI landing page. However, many Crossref links still hit access restrictions or publisher blocks.

### Europe PMC / PMC

Europe PMC produced one accepted PDF in the clean PDF pass and remains valuable for biomedical rows. PMC/Europe PMC XML should be prioritized when available because it is more parseable than PDF.

### Semantic Scholar OpenAccessPdf

Semantic Scholar produced one accepted PDF. It is not the highest-yield route here, but it is useful as a secondary OA locator and as a possible route for crosswalk/snippet search later.

### Source-File Manifesting

The `source_file` layer is critical. Once files are first-class, every later parser and verifier can refer to a stable file ID and SHA-256. This makes it possible to audit whether a level 5 or level 6 claim is grounded in real bytes.

### Identity Gate

The identity gate prevented a major false improvement. Without it, we would have counted 44 PDFs from the broad pass. With it, only 11 were correct. That is the difference between a provenance system and a web downloader.

## What Did Not Work

### Non-Primary Identifier Chasing

Non-primary leads are useful as clues, but dangerous as acquisition anchors. Many corpus rows include related papers, replication papers, reviews, source datasets, or arbitrary DOI URLs. Treating all of those as possible "original paper" identifiers creates false positives.

The fix is:

- Use primary DOI/PMID/PMCID/NCT as default acquisition anchors.
- Preserve non-primary URLs as leads.
- Require identity validation before promotion.
- Do not let a non-primary DOI silently become the represented source.

### Publisher Landing Pages

Publisher landing pages are a major bottleneck. Many return 403, paywall/login HTML, JavaScript challenges, or abstract-only pages. The clean pass saw:

```text
214 HTTP 403 blocked
24 login/paywall HTML
3 CAPTCHA/bot-block pages
7 HTML-not-PDF pages
```

We are not trying to bypass access controls. Bot-blocked pages are logged as blockers, not attacked with spoofing or CAPTCHA workarounds. For those rows, better routes are repository copies, accepted manuscripts, official TDM APIs, institutional/manual access, Internet Archive captures, or author/corpus-maintainer help.

### DOI Resolver PDF Negotiation

Requesting the DOI URL with `Accept: application/pdf` is low-yield. It usually resolves to landing pages, paywalls, or HTML. It is still worth logging as a final cheap attempt, but it should not be expected to solve many rows.

### Metadata-Only Success

Metadata APIs can ground identity but often do not return source bytes. A Crossref/OpenAlex/Semantic Scholar metadata hit is level 4-ish evidence, not level 5. It helps us know what to look for, but it does not prove article text was obtained.

### Full Article Obtained Still Leaves Parsing Work

We now have many level 5 rows, but level 6 remains lower. A full article PDF/XML/HTML may not contain the exact D/N in a simple place. The value may be in a table, supplement, figure, model output, p-value conversion, group count, or a corpus-specific transformation. Level 5 is a source-object win, not a value-verification win.

## Bot Blocks And Access Barriers

The clean primary-identifier run tells us the shape of the barrier. The largest hard failure class is HTTP 403. That usually means the host refused automated access. Some of those may be publisher anti-bot systems. Some may be repository hotlink restrictions. Some may be PDF endpoints requiring a session. The second important barrier is paywall/login HTML: the URL exists, but the PDF is behind subscriber access.

We should log these carefully because they imply different next actions:

- `http_403_blocked`: try repository copies, Internet Archive, manual browser, or official TDM route.
- `login_or_paywall_html`: try institutional/library access, accepted manuscript, Unpaywall alternatives, author manuscript search.
- `captcha_or_bot_block`: do not automate around it; manual browser or alternate route.
- `html_not_pdf`: classify page; may still contain abstract or full article HTML.
- `http_404`: try Wayback, DOI metadata, repository search, or title search.
- `metadata ok but no PDF`: good identity route, poor source-object route.

The project policy is internal-only storage. We download reachable source objects locally, keep the bytes out of git under `data/cache/*`, store route/path/SHA/timestamp/MIME, and publish only metadata plus short relevant evidence windows rather than full documents. That policy supports verification while avoiding redistribution of full-text corpora.

## What The Remaining ~106 Rows Probably Need

The 106 below-level-5 rows are not one problem. They likely fall into several buckets:

1. Grounded DOI rows behind paywalls or publisher blocks.
2. Grounded DOI rows where OA metadata exists but no direct PDF route worked.
3. Rows with weak represented-source identity from corpus assertions.
4. Rows where the represented source might be a preprint, accepted manuscript, or repository copy rather than the publisher VOR.
5. Rows needing historical registry/source-version recovery.
6. Rows where the original paper is not enough because the value is in a supplement or dataset.
7. Rows from anonymized corpora where the paper-ID crosswalk is incomplete.

The next pass should not be "try the same DOI APIs again." We need route-specific escalation:

- OpenAIRE and BASE for institutional repository copies.
- CORE for repository full text.
- Fatcat / Internet Archive Scholar / Wayback for archived PDFs or landing pages.
- Paperclip for indexed PMC/bioRxiv/medRxiv/arXiv full-text discovery.
- Semantic Scholar snippets/datasets for exact text crosswalks.
- OSF/PsyArXiv/SocArXiv for psychology/social-science preprints.
- Dataverse/Zenodo/Figshare/OpenICPSR for datasets and supplements.
- AACT historical snapshots for CT.gov drift.
- Manual library/browser workflow for publisher-blocked VOR PDFs.
- Corpus-author or maintainer contact for anonymized crosswalks.

## What It Would Take To Finish The Last 100

The remaining rows probably cannot all be solved by open web APIs. A realistic plan needs three tracks.

Track 1: automated repository and archive expansion. This means adding OpenAIRE, BASE, CORE, Fatcat, Internet Archive CDX, OSF preprints, Dataverse, Zenodo, Figshare, and maybe Lens/Dimensions if available. Each route needs a candidate ledger and identity gate. Expected lift: moderate. It may recover accepted manuscripts and repository PDFs for paywalled articles.

Track 2: parser/value extraction for existing level 5 rows. This does not acquire new papers, but it may move many current level 5 rows to level 6. Use JATS/XML first, then PDF text extraction, GROBID/Docling/pdfplumber/Camelot, and supplement parsers. Expected lift: high for already mirrored full articles and structured files.

Track 3: human/manual acquisition. For blocked publisher pages, ambiguous corpus rows, or institutional PDFs, a human can use a browser, library access, Zotero, publisher pages, or author contact. The human task should be structured: target DOI/title, failed routes, suspected blocker, acceptable source types, download path, SHA-256, title/DOI confirmation, and whether D/N appears.

The hardest rows are likely the weak corpus assertions and anonymized crosswalks. Those may require corpus maintainer contact or manual reconstruction. We should not pretend automation can infer a represented paper from N/effect/year alone.

## Prompt For Help

We are working on a 300-row D-vs-N evidence-map pilot. Each row represents a plotted effect-size/sample-size dot. We need to trace each dot back to the represented original source and, ideally, exact source text/data proving D and N. Current evidence counts are:

```text
Level 2: 10 external/corpus assertion only
Level 4: 96 independently grounded represented source, but no original source object yet
Level 5: 106 original source object obtained, not yet D/N-verified from that object
Level 6: 88 D/N verified from source
Level >=5: 194/300
Below level 5: 106/300
```

Current full-article objects, counting article text in any form, are:

```text
47 PDF
35 full article XML
13 full article HTML
4 PMC/JATS XML
= 99 full article objects
```

Other source objects include registry JSON, datasets, and supplements. These can verify values, but should not be counted as full articles.

The workflow is implemented in Python/Codex inside a repository. Source manifests are TSVs. Downloaded files are stored locally under `data/cache/*` and gitignored. We do not redistribute full documents. We store routes, paths, SHA-256 hashes, source byte class, identity decisions, and later short relevant evidence windows.

What we already tried for below-level-5 DOI/PMID/PMCID rows:

- Crossref metadata and TDM/full-text links.
- Unpaywall PDF/OA locations.
- OpenAlex locations and PDF URLs.
- Semantic Scholar `openAccessPdf`.
- Europe PMC and PMC routes.
- PubMed eSummary bridge.
- DOI resolver with `Accept: application/pdf`.

An early broad pass downloaded 44 PDFs, but identity validation showed only 11 were the correct represented source. The false positives came from non-primary DOI/URL leads contaminating the acquisition pool, including repeated wrong PDFs such as `10.1090/noti3044`. We fixed this by using primary identifiers only by default and adding a PDF identity gate. The clean pass attempted 113 rows, downloaded 11 PDFs, and all 11 passed identity validation. The clean route successes were:

```text
7 Unpaywall
2 Crossref TDM
1 Europe PMC
1 Semantic Scholar
```

The clean failure profile was:

```text
568 metadata OK / non-download attempt rows
214 HTTP 403 blocked
24 login/paywall HTML
20 HTTP 404
18 HTTP not OK
11 PDF obtained
7 HTML not PDF
3 CAPTCHA/bot-block
```

We need help designing the next concrete acquisition pass for the remaining ~106 below-level-5 rows. Please do not give generic literature-search advice. Propose specific tactics that can be implemented as resolver modules or human work queues. For each tactic, specify:

1. Which rows it targets.
2. Required inputs: DOI, title, PMID, PMCID, NCT, author/year, snippet, source corpus name, etc.
3. Exact API/tool/source to use.
4. What it can return: PDF, XML, HTML, abstract, landing page, supplement, dataset, repository record, archive capture, crosswalk candidate.
5. How to validate identity so we do not accept wrong papers.
6. How to classify the source object in the evidence scale.
7. Expected lift on this type of pilot.
8. Failure modes and how to log them.
9. Which parts should remain manual/human/librarian work.
10. Whether the tactic helps obtain full article text, non-article original evidence, or only identity grounding.

Please prioritize practical lawful/reproducible routes we have not fully exploited yet: OpenAIRE, BASE, CORE, Fatcat / Internet Archive Scholar, Wayback CDX/Memento, OSF/PsyArXiv/SocArXiv, Dataverse, Zenodo, Figshare, OpenICPSR, Paperclip full-text search, Semantic Scholar snippets/datasets, AACT historical snapshots, PubMed/PMC/Europe PMC bulk sources, Crossref relationship metadata, and Zotero/translation-server-assisted manual capture. Also tell us what it would take to solve the rows blocked by publisher 403/paywall/CAPTCHA responses, and what metadata a human should collect when manual library/browser access is required.
