# Level-6 Text Candidate Snippets

- Sample rows: 300
- Parser routes attempted: html_first, structured_xml_first
- PDF pages cap if `pdf_cascade` is enabled: 5
- Source files attempted: 52
- Snippet/status rows written: 72
- Linked source-result rows with at least one label or numeric candidate hit: 16

## Candidate Status

- `text_extracted_no_label_or_numeric_hit`: 36
- `numeric_hit`: 25
- `label_hit`: 11

## Interpretation

- Candidate hits are not level-6 evidence. They are triage snippets for the next verifier pass; promotion still requires exact source-result support and D/N recomputation.
- Numeric-only hits are especially weak unless the surrounding snippet identifies the same outcome/table/contrast.

## Output Files

- `data/derived/effect_inflation_dataset/schema_pilot/level6_text_candidate_snippets_sample_300.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/level6_text_candidate_snippets_summary_sample_300.tsv`
