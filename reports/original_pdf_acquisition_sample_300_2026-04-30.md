# Original PDF Acquisition Pilot

- Sample rows: 300
- Rows below level 5 with DOI/PMID/PMCID route attempted: 113
- Valid PDFs obtained: 11
- Unpaywall route enabled: true

## Route Successes

- `sr_2ef5e9c7214d` via `unpaywall_pdf`; `data/cache/original_pdf_acquisition/sample_300/sr_2ef5e9c7214d__unpaywall_pdf__63388ab3f471.pdf`
- `sr_57e119b02525` via `europepmc_pdf`; `data/cache/original_pdf_acquisition/sample_300/sr_57e119b02525__europepmc_pdf__7c942bd6e75e.pdf`
- `sr_05a96a248d34` via `unpaywall_pdf`; `data/cache/original_pdf_acquisition/sample_300/sr_05a96a248d34__unpaywall_pdf__586f3885f20a.pdf`
- `sr_10e682ba553b` via `unpaywall_pdf`; `data/cache/original_pdf_acquisition/sample_300/sr_10e682ba553b__unpaywall_pdf__9ecaff1a6d63.pdf`
- `sr_2ead36cae8e2` via `unpaywall_pdf`; `data/cache/original_pdf_acquisition/sample_300/sr_2ead36cae8e2__unpaywall_pdf__fefacc929b57.pdf`
- `sr_307943984453` via `crossref_tdm_pdf`; `data/cache/original_pdf_acquisition/sample_300/sr_307943984453__crossref_tdm_pdf__35bbb32c61a9.pdf`
- `sr_30b176b2d082` via `semantic_scholar_openaccess_pdf`; `data/cache/original_pdf_acquisition/sample_300/sr_30b176b2d082__semantic_scholar_openaccess_pdf__6e232b5f1ac6.pdf`
- `sr_644891607462` via `unpaywall_pdf`; `data/cache/original_pdf_acquisition/sample_300/sr_644891607462__unpaywall_pdf__c7d9019b1222.pdf`
- `sr_a182ef5b0da7` via `unpaywall_pdf`; `data/cache/original_pdf_acquisition/sample_300/sr_a182ef5b0da7__unpaywall_pdf__586f3885f20a.pdf`
- `sr_bbf5b92dab8e` via `crossref_tdm_pdf`; `data/cache/original_pdf_acquisition/sample_300/sr_bbf5b92dab8e__crossref_tdm_pdf__f91d5fb57bbc.pdf`
- `sr_d30c0407b24b` via `unpaywall_pdf`; `data/cache/original_pdf_acquisition/sample_300/sr_d30c0407b24b__unpaywall_pdf__8087ca98974b.pdf`

## Failure Profile

- `ok`: 568
- `http_403_blocked`: 214
- `login_or_paywall_html`: 24
- `http_404:`: 20
- `http_not_ok`: 18
- `pdf_obtained`: 11
- `html_not_pdf`: 7
- `captcha_or_bot_block`: 3

## Interpretation

- A valid PDF here is an acquisition candidate, not level-6 evidence. It still needs identity checking, access/share-scope tagging, source-file manifest promotion, parsing, exact locator support, and D/N verification.
- By default this pass uses primary identifiers only. Non-primary grounding URLs can be enabled for exploratory chasing with `ORIGINAL_PDF_INCLUDE_NONPRIMARY_IDENTIFIERS=true`, but they must pass the PDF identity check before promotion.
- Metadata rows are included so route failures remain visible rather than disappearing behind the first successful or blocked URL.

## Output Files

- `data/derived/effect_inflation_dataset/schema_pilot/original_pdf_acquisition_attempts_sample_300.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/original_pdf_acquisition_summary_sample_300.tsv`
